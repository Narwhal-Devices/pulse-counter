import numpy as np
import serial
import serial.tools.list_ports
import queue
import threading
import time
from . import transcode


class PulseCounter():
    def __init__(self):

        #setup serial port
        self.ser = serial.Serial()
        self.ser.timeout = 0.1          #block for 100ms second
        self.ser.writeTimeout = 1     #timeout for write
        self.ser.baudrate = 12000000
        self.ser.port = 'COM6'

        self.counter_queue = queue.Queue()
        self.echo_queue = queue.Queue()
        self.close_readthread_event = threading.Event()
        self.read_thread_killed_itself = False

        self.connected = False
        self.connection_trys = 0
        self.valid_ports = []
        
        self.connect_serial()

    def connect_serial(self):
        self.connection_trys += 1
        if self.connection_trys >= 5:
            print('Could not connect device')
            return
        if self.valid_ports:
            # now try a port
            comport = self.valid_ports.pop(0)
            self.ser.port = comport.device
            try:
                self.ser.open()
            except Exception as ex:
                #if port throws an error on open, wait a bit, then try a new one
                time.sleep(0.1)
                self.connect_serial()
                return
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            # self.serial_thread.start()
            self.serial_read_thread = threading.Thread(target=self.monitor_serial)
            self.serial_read_thread.start()
            self.tested_authantication_byte = np.random.bytes(1)
            self.write_command(transcode.encode_echo(self.tested_authantication_byte))
            self.check_authantication_byte()
        else:
            # if there are no ports left in the list, add any valid ports to the list  
            comports = list(serial.tools.list_ports.comports())
            for comport in comports:
                if 'vid' in vars(comport) and 'pid' in vars(comport):
                    if vars(comport)['vid'] == 1027 and vars(comport)['pid'] == 24592:
                        self.valid_ports.append(comport)
            if self.valid_ports:
                self.connect_serial()
            else:
                print('Hardware not found, searching for hardware...')
                time.sleep(1)
                self.connect_serial()

    def check_authantication_byte(self):
        echoed_bytes = []
        while not self.echo_queue.empty:
            echoed_bytes.append(self.echo_queue.get(block=False)['echoed_byte'])
        try:
            message = self.echo_queue.get(timeout=1)
            echoed_bytes.append(message['echoed_byte'])
        except queue.Empty as ex:
            pass
        if self.tested_authantication_byte in echoed_bytes:
            # print('authentication success')
            self.set_holdoff(10E-9)
            self.write_command(transcode.encode_settings(enable_counter=True, enable_send_counts=True))
            self.connected = True
            self.connection_trys = 0
        else:
            print('authentication failed')
            self.safe_close_serial_port()
            time.sleep(1)
            print('attemping to reconnect')
            self.connect_serial()

    def write_command(self, encoded_command):
        # not really sure if this is the correct place to put this. 
        # basically, what i need is that if the read_thread shits itself, the main thread will automatically safe close the connection, and then try to reconnect.
        if self.read_thread_killed_itself:
            self.safe_close_serial_port()
            self.connect_serial()
        try:
            self.ser.write(encoded_command)
        except Exception as ex:
            print('write command failed')
            self.safe_close_serial_port()

    def monitor_serial(self):
        self.read_thread_killed_itself = False
        remaining_data = np.array((), dtype=np.uint8)
        while not self.close_readthread_event.is_set():
            try:
                if (bytes_waiting := self.ser.in_waiting):
                    new_data = self.ser.read(bytes_waiting)
                else:
                    new_data = self.ser.read(1)
            except serial.serialutil.SerialException as ex:
                self.close_readthread_event.set()
                self.read_thread_killed_itself = True
                break
            new_data_arr = np.array(list(new_data), dtype=np.uint8)
            counts, counts_idx, other_messages, other_messages_idx, remaining_data, bytes_dropped = transcode.quick_decode(remaining_data, new_data_arr)

            if bytes_dropped:
                print('bytes dropped')

            if counts_idx:
                list(map(self.counter_queue.put, counts[:counts_idx]))

            if other_messages_idx:
                for message_arr in other_messages[:other_messages_idx]:
                    message_identifier = message_arr[0]
                    message_bytes = bytes(message_arr[1:transcode.msgin_decodeinfo[message_identifier]['message_length']])
                    message = transcode.msgin_decodeinfo[message_identifier]['decode_function'](message_bytes)
                    if message_identifier == transcode.msgin_identifier['devicestatus']:
                        print(message)
                    elif message_identifier == transcode.msgin_identifier['error']:
                        print(message)
                    elif message_identifier == transcode.msgin_identifier['echo']:
                        # print(message)
                        self.echo_queue.put(message)
                    elif message_identifier == transcode.msgin_identifier['print']:
                        print(message)

    def safe_close_serial_port(self):
        self.close_readthread_event.set()
        self.serial_read_thread.join()
        self.ser.close()
        self.connection_trys = 0
        self.connected = False

    def close(self):
        self.disable_counter()
        self.disable_send()
        self.safe_close_serial_port()

    def zero_counter(self):
        command = transcode.encode_settings(zero_pulse_timer=True)
        self.write_command(command)

    def purge_memory(self):
        command = transcode.encode_settings(purge_memory=True)
        self.write_command(command)
        with self.counter_queue.mutex:
            self.counter_queue.queue.clear()

    def enable_send(self):
        command = transcode.encode_settings(enable_send_counts=True)
        self.write_command(command)

    def disable_send(self):
        command = transcode.encode_settings(enable_send_counts=False)
        self.write_command(command)

    def enable_counter(self):
        command = transcode.encode_settings(enable_counter=True)
        self.write_command(command)

    def disable_counter(self):
        command = transcode.encode_settings(enable_counter=False)
        self.write_command(command)

    def set_holdoff(self, holdoff):
        num = min(holdoff, 1.3)
        num = max(holdoff, 10E-9)
        cycles = round(num/5E-9)
        command = transcode.encode_settings(holdoff_time=int(cycles-2))
        self.write_command(command)
    
    def get_memory_usage(self):
        command = transcode.encode_settings(request_status=True)
        self.write_command(command) 

    def software_trigger(self):
        #This internally forces the device to record the counts. The softeware equivalent of the hardware trigger.
        command = transcode.encode_settings(request_counter_value=True)
        self.write_command(command)

    def get_counts(self, timeout=None):
        try:
            counts = self.counter_queue.get(timeout=timeout)
        except queue.Empty as ex:
            return None
        return counts




if __name__ == '__main__':
    # This is the main thread. I have to let this keep doing stuff.

    # setup experiment

    #setup counter
    counter = PulseCounter()
    counter.purge_memory()

    for a in range(500000):
        counts = counter.get_counts(timeout=1)
        if a % 1000 == 0:
            print(counts)

    counter.close()

    #Start the experiment
    
    #constantly read the counter from the pulse counter, and update plots. Resize etc.

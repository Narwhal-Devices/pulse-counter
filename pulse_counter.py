from numba.cuda.errors import normalize_kernel_dimensions
import numpy as np
import pathlib
import serial
import serial.tools.list_ports
import struct
import queue
import threading
import time
import transcode


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
        self.authantication_byte = None
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
        bytes_dropped = False
        self.read_thread_killed_itself = False
        while not self.close_readthread_event.is_set():
            try:
                byte_message_identifier = self.ser.read(1)
            except serial.serialutil.SerialException as ex:
                self.close_readthread_event.set()
                self.read_thread_killed_itself = True
                break
            
            if byte_message_identifier:
                message_identifier, = struct.unpack('B', byte_message_identifier)
                if message_identifier in transcode.msgin_decodeinfo.keys():
                    decode_function = transcode.msgin_decodeinfo[message_identifier]['decode_function']
                    message_length = transcode.msgin_decodeinfo[message_identifier]['message_length'] - 1
                    try:
                        byte_message = self.ser.read(message_length)
                    except serial.serialutil.SerialException as ex:
                        self.close_readthread_event.set()
                        self.read_thread_killed_itself = True
                        break
                    if len(byte_message) == message_length:
                        message = decode_function(byte_message)
                        #Now decide what you actually want to do with the different messages.
                        if message_identifier == transcode.msgin_identifier['error']:
                            print(message)
                        elif message_identifier == transcode.msgin_identifier['echo']:
                            self.authantication_byte = message['echoed_byte']
                            # print(message)
                            self.echo_queue.put(message)
                        elif message_identifier == transcode.msgin_identifier['print']:
                            print(message)
                        elif message_identifier == transcode.msgin_identifier['devicestatus']:
                            print(message)
                            print(self.ser.in_waiting)
                        elif message_identifier == transcode.msgin_identifier['pulserecord']:
                            # print(message)  
                            self.counter_queue.put((message['pulse_count'], bytes_dropped))
                            bytes_dropped = False
                            # print(self.ser.in_waiting)
                else:
                    bytes_dropped = True

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

    def get_counts(self, timeout=None, indicate_bytes_dropped = False):
        try:
            counts, bytes_dropped = self.counter_queue.get(timeout=timeout)
        except queue.Empty as ex:
            if indicate_bytes_dropped:
                return None, None
            else:
                return None
        if indicate_bytes_dropped:
            return counts, bytes_dropped
        else:
            return counts


if __name__ == '__main__':
    # This is the main thread. I have to let this keep doing stuff.

    # setup experiment

    #setup counter
    counter = PulseCounter()
    counter.purge_memory()
    # time.sleep(10)
    # t0 = time.time()
    for a in range(50000):
        counts, bytes_dropped = counter.get_counts(timeout=1, indicate_bytes_dropped=True)
        # print(counts)
        if bytes_dropped:
            print('booo bytes dropped')

        # if a % 1000 == 0:
        #     counter.get_memory_usage()
    # t1 = time.time()
    # print((t1-t0)/1000)

    # while (counts := counter.get_counts(timeout=0.1)) is not None:
    #     print(counts)
    # for a in range(5):
    #     print(counter.get_counts(timeout=1))


    # counter.write_command(transcode.encode_echo('a'.encode()))


    counter.close()

    #Start the experiment
    
    #constantly read the counter from the pulse counter, and update plots. Resize etc.

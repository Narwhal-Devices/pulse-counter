import zmq
import random
import sys
import time
import serial
import multiprocessing

class MainSide():
    def __init__(self):
        print('boo')
        # direct passthrough sender socket
        self.dpss_port = "5556"
        self.dpss_context = zmq.Context()
        self.dpss_socket = self.dpss_context.socket(zmq.PAIR)
        self.dpss_socket.bind("tcp://*:%s" % self.dpss_port)

        # direct passthrough reciever socket
        self.dprs_port = "5557"
        self.dprs_context = zmq.Context()
        self.dprs_socket = self.dprs_context.socket(zmq.PAIR)
        self.dprs_socket.bind("tcp://*:%s" % self.dprs_port)
        # control socket

        # info return socket
    def test_send(self):
        print('testing')
        for txt in range(10):
            sndtxt = str(txt).encode()
            self.dpss_socket.send(sndtxt)
            print(txt)
            # returned = self.dprs_socket.recv()
            # print(returned)
            self.dpss_socket.send('4'.encode())
            self.dpss_socket.send('end'.encode())

class BufferSide():
    def __init__(self):
        print('hoo')
        # direct passthrough sender socket
        self.dpss_port = "5556"
        self.dpss_context = zmq.Context()
        self.dpss_socket = self.dpss_context.socket(zmq.PAIR)
        self.dpss_socket.connect("tcp://localhost:%s" % self.dpss_port)

        # direct passthrough reciever socket
        self.dprs_port = "5557"
        self.dprs_context = zmq.Context()
        self.dprs_socket = self.dprs_context.socket(zmq.PAIR)
        self.dprs_socket.connect("tcp://localhost:%s" % self.dprs_port)
        # control socket

        # info return socket

        while True:
            msg = self.dpss_socket.recv()
            print(msg)
            if msg == 'end'.encode():
                break
        # while (to_send := self.dpss_socket.recv()) != 'end'.encode():
        #     # to_send = dpss_socket.recv()
        #     print('jksdj', to_send)
        #     # self.dprs_socket.send(to_send)

class BufferedSerial():
    def __init__(self):

        # self.setup_main_process_components()
        # self.buffer_process = multiprocessing.Process(target=self.setup_buffer_process_component, args=(1,))
        # self.buffer_process.start()
        self.main_side = MainSide()

        self.buffer_process = multiprocessing.Process(target=BufferSide)
        self.buffer_process.start()

        self.main_side.test_send()
        # self.test_send()

    # def setup_main_process_components(self):
    #     print('setting up main process')
        # direct passthrough sender socket
        # self.dpss_port = "5556"
        # self.dpss_context = zmq.Context()
        # self.dpss_socket = self.dpss_context.socket(zmq.PAIR)
        # self.dpss_socket.bind("tcp://*:%s" % self.dpss_port)

        # # direct passthrough reciever socket
        # self.dprs_port = "5557"
        # self.dprs_context = zmq.Context()
        # self.dprs_socket = self.dprs_context.socket(zmq.PAIR)
        # self.dprs_socket.bind("tcp://*:%s" % self.dprs_port)
        # # control socket

        # # info return socket

    # def test_send(seld):
    #     print('testing')
        # for txt in range(10):
        #     self.dpss_socket.send(str(txt).encode())
        #     returned = dprs_socket.recv()
        #     print(returned)

        #     self.dpss_socket.send('end'.encode())



    # def setup_buffer_process_component(self, a):
    #     print('setting up buffer process', a)
        # # direct passthrough sender socket
        # self.dpss_port = "5556"
        # self.dpss_context = zmq.Context()
        # self.dpss_socket = self.dpss_context.socket(zmq.PAIR)
        # self.dpss_socket.connect("tcp://localhost:%s" % dpss_port)

        # # direct passthrough reciever socket
        # self.dprs_port = "5557"
        # dprs_context = zmq.Context()
        # self.dprs_socket = self.dprs_context.socket(zmq.PAIR)
        # self.dprs_socket.connect("tcp://localhost:%s" % self.dprs_port)
        # # control socket

        # # info return socket

        # while (to_send := self.dpss_socket.recv()) != 'end'.encode():
        #     # to_send = dpss_socket.recv()
        #     self.dprs_socket.send(to_send)


        # serial port settings
        # (port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None, exclusive=None)

        # direct passthrough sender socket

        # direct passthrough reciever socket

        # control socket

        # info return socket


        '''
        this whole thing runs in a different process, so I have to make another bit that runs in the main process
        '''
if __name__ == '__main__':
    buf = BufferedSerial()



        # buffer_process = multiprocessing.Process(target=self.setup_buffer_process_component)
        # buffer_process.start()
import queue
import threading
import time


# def read_thread(message_queue, close_readthread_event):
#     message = 0
#     while not close_readthread_event.is_set():
#         message += 1
#         message_queue.put(message)
#         time.sleep(0.1)
#     print('read thread is closing', threading.get_ident())


# def close_read_thread(close_readthread_event):
#     print('close function was called', threading.get_ident())
#     close_readthread_event.set()


# if __name__ == "__main__":
#     message_queue = queue.Queue()
#     close_readthread_event = threading.Event()

#     readthread = threading.Thread(target=read_thread, args=(message_queue, close_readthread_event))
#     readthread.start()

#     quit_timer = threading.Timer(1, close_read_thread, args=(close_readthread_event,))
#     quit_timer.start()

#     while not close_readthread_event.is_set():
#         if not message_queue.empty():
#             message = message_queue.get()
#             print(message)

#     # while not message_queue.empty():
#     #     message = message_queue.get()
#     #     print(message)

#     # close_readthread_event.set()
#     readthread.join()
#     print('main thread is closing', threading.get_ident())

# class MyDevice():
#     def __init__(self):
#         self.message_queue = queue.Queue()
#         self.close_readthread_event = threading.Event()

#         self.readthread = threading.Thread(target=self.read_thread, args=(self.message_queue, self.close_readthread_event))
#         self.readthread.start()

#         self.quit_timer = threading.Timer(0.5, self.close_read_thread, args=(self.close_readthread_event,))
#         self.quit_timer.start()

#         # do stuff
#         while not self.close_readthread_event.is_set():
#             if not self.message_queue.empty():
#                 message = self.message_queue.get()
#                 print(message)

#         # finish up
#         self.readthread.join()
#         print('main thread is closing', threading.get_ident())

#     def read_thread(self, message_queue, close_readthread_event):
#         message = 0
#         while not close_readthread_event.is_set():
#             message += 1
#             message_queue.put(message)
#             time.sleep(0.1)
#         print('read thread is closing', threading.get_ident())


#     def close_read_thread(self, close_readthread_event):
#         print('close function was called', threading.get_ident())
#         close_readthread_event.set()


class MyDevice():
    '''like all calsses, you can either pass argumens to the methods, or save the variables as attributes of the calss'''
    def __init__(self):
        self.message_queue = queue.Queue()
        self.close_readthread_event = threading.Event()

        self.readthread = threading.Thread(target=self.read_thread)
        self.readthread.start()

        self.quit_timer = threading.Timer(0.5, self.close_read_thread)
        self.quit_timer.start()

        # do stuff
        while not self.close_readthread_event.is_set():
            if not self.message_queue.empty():
                message = self.message_queue.get()
                print(message)

        # finish up
        self.readthread.join()
        print('main thread is closing', threading.get_ident())

    def read_thread(self):
        message = 0
        while not self.close_readthread_event.is_set():
            message += 1
            self.message_queue.put(message)
            time.sleep(0.1)
        print('read thread is closing', threading.get_ident())


    def close_read_thread(self):
        print('close function was called', threading.get_ident())
        self.close_readthread_event.set()


# class MyDevice():
#     '''And I don't have to use events if everything is kept within the class, but it is probably good practise to use events anyway.'''
#     def __init__(self):
#         self.message_queue = queue.Queue()
#         self.close_readthread_event = False

#         self.readthread = threading.Thread(target=self.read_thread)
#         self.readthread.start()

#         self.quit_timer = threading.Timer(0.5, self.close_read_thread)
#         self.quit_timer.start()

#         # do stuff
#         while not self.close_readthread_event:
#             if not self.message_queue.empty():
#                 message = self.message_queue.get()
#                 print(message)

#         # finish up
#         self.readthread.join()
#         print('main thread is closing', threading.get_ident())

#     def read_thread(self):
#         message = 0
#         while not self.close_readthread_event:
#             message += 1
#             self.message_queue.put(message)
#             time.sleep(0.1)
#         print('read thread is closing', threading.get_ident())


#     def close_read_thread(self):
#         print('close function was called', threading.get_ident())
#         self.close_readthread_event = True


if __name__ == "__main__":

    device = MyDevice()


import queue
import time
import threading
import bluetooth
import math
import random
import socket
import subprocess       # for Raspberry Pi shutdown
import os


class BluetoothServer:
    # run = True  # Argument for shuting down all loops at the same time with input from one device.

    def __init__(self, list_of_variables_for_threads):
        # List of all variables from main to class.
        self.list_of_variables_for_threads = list_of_variables_for_threads
        self.go = list_of_variables_for_threads["go"]
        # Bluetooth variables
        self.client_list = []         # list for each connected device, sockets
        self.address_list = []        # list for mac-adresses from each connected device
        # self.read_thread_list = []     # list for threads to recieve from each device
        self.host = ""
        self.port = 1
        self.client = None
        # Setup server for bluetooth communication
        self.server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server.setblocking(0)  # Makes server.accept() non-blocking, used for "poweroff"
        # TEMP: Data from radar used to make sure data can be accepted between threads
        # Queue from radar class to test if queue communication work
        self.RR_final_queue = list_of_variables_for_threads["RR_final_queue"]
        self.RTB_final_queue = list_of_variables_for_threads["RTB_final_queue"]
        self.run_measurement = list_of_variables_for_threads["run_measurement"]
        self.start_write_to_csv_time = list_of_variables_for_threads["start_write_to_csv_time"]
        self.initiate_write_heart_rate = list_of_variables_for_threads["initiate_write_heart_rate"]
        print('Bluetooth Socket Created')
        try:
            self.server.bind((self.host, self.port))
            print("Bluetooth Binding Completed")
        except:
            print("Bluetooth Binding Failed")

        # Can be accessed from main-program to wait for it to close by .join()
        self.connect_device_thread = threading.Thread(
            target=self.connect_device)  # Starts thread which accepts new devices
        self.connect_device_thread.start()

    def app_data(self):  # The main loop which takes data from processing and sends data to all clients
        while self.go:
            pass
            # while len(self.client_list) == 0:
            #    time.sleep(1)
            #    continue
            # self.schmitt_to_app()
            # self.real_time_breating_to_app()
            # data = self.add_data(2)  # TEMP: Makes random data for testing of communication
            # data_pulse, data_breath = data.split(' ')  # Splits data in pulse and heart rate
            # self.write_data_to_app(data_pulse, 'heart rate')  # Sends pulse to app
            # self.write_data_to_app(data_breath, 'breath rate')  # Sends heart rate to app

    def schmitt_to_app(self):
        try:
            # TEMP: Takes data from Schmitt trigger
            while len(self.RR_final_queue) == 0 and self.go:
                time.sleep(0.001)
            schmitt_data = self.RR_final_queue.get_nowait()
            # print("got data from queue")
            self.write_data_to_app(schmitt_data, 'breath rate')
        # schmitt_data = ' BR ' + schmitt_data + ' '      # TODO ändra till RR istället för BR i appen också
        # print("made string")
        # self.send_data(schmitt_data)
        # print("sent data")
        except:
            print("timeout RR queue")

    def real_time_breating_to_app(self):
        try:
            # while self.RTB_final_queue.empty() and self.go:
            #    time.sleep(0.005)
            # TEMP: Takes data from filtered resp.rate
            real_time_breating_to_app = self.RTB_final_queue.get_nowait()
            # print("Real time breathing to app {}".format(real_time_breating_to_app))
            self.write_data_to_app(real_time_breating_to_app, 'real time breath')
            if not self.RR_final_queue.empty():
                schmitt_data = self.RR_final_queue.get_nowait()
                self.write_data_to_app(schmitt_data, 'breath rate')

        except:
            print(len(self.RR_final_queue))

    def connect_device(self):
        #os.system("echo 'power on\nquit' | bluetoothctl")  # Startup for bluetooth on rpi TODO
        thread_list = []  # List which adds devices
        self.server.listen(7)  # Amount of devices that can simultaniously recive data.
        while self.go:
            # Loop which takes listens for a new device, adds it to our list
            # and starts a new thread for listening on input from device
            try:
                c, a = self.server.accept()
            except:
                if self.go == False:
                    break
                # print("Still accepting new phones" + str(error))
                continue
            self.client_list.append(c)
            self.address_list.append(a)
            # one thread for each connected device
            thread_list.append(threading.Thread(target=self.read_device))
            thread_list[-1].start()
            print(thread_list[-1].getName())
            print(thread_list[-1].isAlive())
            print("New client: ", a)

        print("Out of while True in connect device")
        # Gracefully close all device threads
        for thread in thread_list:
            print(str(thread.getName()) + str(thread.isAlive()))
            thread.join()
            print(str(thread.getName()) + " is closed")
        print("End of connect_device thread")

    def read_device(self):
        c = self.client_list[-1]  # Takes last added device and connects it.
        print(c)
        print(self.address_list[-1])
        try:
            while self.go:
                data = c.recv(1024)  # Input argument from device
                data = data.decode('utf-8')
                data = data.strip()
                print(data)
                # When device sends "poweroff" initiate shutdown by setting go to false, removing all clients and closing all threads.
                if data == 'poweroff':
                    print("Shutdown starting")
                    try:
                        #self.go = []
                        #self.list_of_variables_for_threads["go"] = self.go.pop(0)
                        #list_of_variables_for_threads["go"] = go.pop(0)
                        self.go.pop(0)
                        print("go= " + str(self.go))
                        for client in self.client_list:
                            print('try to remove client ' +
                                  str(self.address_list[self.client_list.index(client)]))
                            client.close()
                            print('remove client ' +
                                  str(self.address_list[self.client_list.index(client)]))
                        self.server.close()
                        print("server is now closed")
                        os.system("echo 'power off\nquit' | bluetoothctl")  # TODO
                    except Exception as error:
                        print("exception in for-loop in read_device: " + str(error))
                if not self.go:
                    print("Shutdown starting")
                    try:
                        #self.go = []
                        #self.list_of_variables_for_threads["go"] = self.go.pop(0)
                        #list_of_variables_for_threads["go"] = go.pop(0)
                        # self.go.pop(0)
                        print("go= " + str(self.go))
                        for client in self.client_list:
                            print('try to remove client ' +
                                  str(self.address_list[self.client_list.index(client)]))
                            client.close()
                            print('remove client ' +
                                  str(self.address_list[self.client_list.index(client)]))
                        self.server.close()
                        print("server is now closed")
                        os.system("echo 'power off\nquit' | bluetoothctl")  # TODO
                    except Exception as error:
                        print("exception in for-loop in read_device: " + str(error))

                elif data == 'startMeasure':
                    self.run_measurement.append(c)
                    self.list_of_variables_for_threads["run_measurement"] = self.run_measurement
                    print("Device added")

                elif data == 'stopMeasure':
                    if c in self.run_measurement:
                        self.run_measurement.remove(c)
                        self.list_of_variables_for_threads["run_measurement"] = self.run_measurement
                        print("Device removed")
                elif data == 'write':
                    print("Bluetooth Write started")
                    self.initiate_write_heart_rate.append(0)
                    self.list_of_variables_for_threads["initiate_write_heart_rate"] = self.initiate_write_heart_rate
                    self.start_write_to_csv_time = time.time()
                    self.list_of_variables_for_threads["start_write_to_csv_time"] = self.start_write_to_csv_time

                    # self.initiate_write_heart_rate

        except Exception as error:
            print("last exception read_device: " + str(error))
            c.close()
            print('remove client: ' + str(self.address_list[self.client_list.index(c)]))
            if c in self.run_measurement:
                self.run_measurement.remove(c)
            self.client_list.remove(c)

    def write_data_to_app(self, data, data_type):
        # print(data + ' ' + data_type)
        if data_type == 'heart rate':
            string = ' HR ' + str(data) + ' '
            # print(string)
            self.send_data(string)
        elif data_type == 'breath rate':
            string = ' RR ' + str(data) + ' '
            # print(string)
            self.send_data(string)
        elif data_type == 'real time breath':
            string = ' RTB ' + str(data) + ' '
            self.send_data(string)

    def send_data(self, write):
        # print('Send data: ' + write)
        for client in self.client_list:  # Send the same data to all clients connected
            try:
                client.send(write.encode('utf-8'))      # write.encode('utf-8')
            except Exception as error:
                print("Error send_data" + str(error))

    def add_data(self, i):  # TEMP: Make data somewhat random.
        data = [70 + math.sin(i), 20 + math.sin(i+math.pi/4)]
        noise = random.random()
        data[0] += 5*(noise - 0.5)
        noise = random.random()
        data[1] += noise
        data[0] = round(data[0])
        data[1] = round(data[1])
        return str(data[0]) + ' ' + str(data[1])

    # def get_data_from_queue(self):
    #     self.send_to_app_queue.put(self.add_data(1))
    #     return self.send_to_app_queue.get()

    # @staticmethod  # Test to send run variable to other threads, does not work yet.
    # def get_run(self):
    #    return self.run

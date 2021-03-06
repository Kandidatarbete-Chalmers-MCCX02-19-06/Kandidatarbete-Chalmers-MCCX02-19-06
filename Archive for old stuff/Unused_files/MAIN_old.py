import time
import threading
import numpy as np
import queue

import Radar

# Bluetooth imports
import bluetooth
import math
import random

# Bluetooth variables
clientList = []         # list for each connected device, sockets
addressList = []        # list for mac-adresses from each connected device
readThreadList = []     # list for threads to recieve from each device
#sinvalue = 0
run = True
test_queue = queue.Queue()
host = ""
port = 1  # Raspberry Pi uses port 1 for Bluetooth Communication

server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
print('Bluetooth Socket Created')
try:
    server.bind((host, port))
    print("Bluetooth Binding Completed")
except:
    print("Bluetooth Binding Failed")

print(hex(id(server)))
# Main method for initiating and running radar measurements, signal processing and sending data through bluetooth to application.
def main():
    global server
    global run
    print(hex(id(server)))
    radar_queue = queue.Queue()
    interrupt_queue = queue.Queue()
    # heart_rate_queue = queue.Queue()
    # resp_rate_queue = queue.Queue()

    radar = Radar.Radar(radar_queue, interrupt_queue)
    radar.start()
    timeout = time.time() + 10 * 60

    # signalprocessing = signalprocessing.HeartRate(radar_queue,heart_rate_queue,resp_rate_queue)
    # signalprocessing.start()

    # bluetooth = Bluetooth(heart_rate_queue,resp_rate_queue)
    # bluetooth.start()
    # bluetooth send data
    # for i in range(1, 2000):
    #     time.sleep(1)
    #     while len(clientList) == 0 and run == True:
    #         pass
    #     data = addData(sinvalue)
    #     # print('Write data: ' + data)
    #     data_pulse, data_breath = data.split(' ')
    #     write_data_to_app(data_pulse, 'heart rate')
    #     write_data_to_app(data_breath, 'breath rate')
    #     sinvalue += 0.157
    for i in range(1, 2000):
        time.sleep(1)
        if time.time() > timeout:
            interrupt_queue.put(1)
        while len(clientList) == 0 and go == True:
            pass
        data = getDatafromQueue(test_queue)
        print('Write data: ' + data)
        data_pulse, data_breath = data.split(' ')
        write_data_to_app(data_pulse, 'heart rate')
        write_data_to_app(data_breath, 'breath rate')
        #sinvalue += 0.157

    server.close()
    print("SLUT")
    #TODO Stänga ner raspberry
    ConnectDevicesThread.join()     # Waits for the thread to close. Implies all ReadDeviceThreads are also closed.
    subprocess.call(["sudo", "shutdown", "-h", "now"])       # shutdown of Raspberry Pi



# Bluetooth functions
def write_data_to_app(data, data_type):
    # print(data + ' ' + data_type)
    if data_type == 'heart rate':
        string = ' HR ' + data + ' '
        # print(string)
        send_data(string)
    elif data_type == 'breath rate':
        string = ' BR ' + data + ' '
        # print(string)
        send_data(string)
    elif data_type == 'real time breath':
        string = ' RTB ' + data + ' '
        send_data(string)


def send_data(write):
    print('Send data: ' + write)
    for client in clientList:
        # print(addressList[clientList.index(client)])
        # print("Length " + str(len(clientList)))
        try:
            client.send(write.encode('utf-8'))  # write.encode('utf-8')
        except:
            print("Error")

def addData(i):
    data = [70 + math.sin(i), 20 + math.sin(i+math.pi/4)]
    noise = random.random()
    data[0] += 5*(noise - 0.5)
    noise = random.random()
    data[1] += noise
    data[0] = round(data[0])
    data[1] = round(data[1])
    return str(data[0]) + ' ' + str(data[1])

def getDatafromQueue(test_queue):
    test_queue.put(addData(1))
    print(test_queue.get())
    return test_queue.get()


class ConnectDevicesThread(threading.Thread):
    def __init__(self):
        super(ConnectDevicesThread, self).__init__()
        server.listen(7)

    def run(self):
        while go:
            c, a = server.accept()
            clientList.append(c)
            addressList.append(a)
            readThreadList.append(ReadDeviceThread(c))       # one thread for each connected device
            readThreadList[len(readThreadList)-1].start()
            print("New client: ", a)

        for thread in readThreadList:       # Makes sure that all our client threads are closed before exiting thread
            thread.join()
            print(thread + " is closed")


class ReadDeviceThread(threading.Thread):
    client = None
    def __init__(self, client):
        self.client = client
        super(ReadDeviceThread, self).__init__()

    def run(self):
        try:
            while go:
                data = self.client.recv(1024)       # important to write self.client everywhere in the class/thread
                print(data.decode('utf-8'))
                if data.decode('utf-8') == 'poweroff':
                    # TODO Erik: Power off python program and Raspberry Pi
                    go = False
                    for client in clientList:
                        client.close()
                        clientList.remove(client)
        except:
            print("exception")
            self.client.close()
            print('remove client: ' + str(addressList[clientList.index(self.client)]))
            clientList.remove(self.client)


if __name__ == "__main__":
    main()

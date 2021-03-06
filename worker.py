import threading
import socket
import time
import pickle
import numpy as np
from include import *
import sys
import os
import statistics

host = HOST
serverPort = SERVER_PORT_WORKERS


def pingServer():
    while True:
        if msgServer("PING"):
            time.sleep(PING_SLEEP)
        else:
            os._exit(1)


def msgServer(msg):
    # Connecting to server port and sending a message
    try:
        connectServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connectServer.connect((host, serverPort))
        dumpMsg = pickle.dumps([msg, workerPort])
        connectServer.send(dumpMsg)
    except Exception as e:
        print("Error with connection socket with server: " + str(e))
        connectServer.close()
        return False

    connectServer.close()
    return True


def handleDataFromClient():
    while True:
        try:
            client, address = workerServer.accept()
        except Exception as e:
            print("Error accepting client connection: " + str(e))
            client.close()
            continue

        # We tell the server we are not ready
        if not msgServer("No"):
            client.close()
            os._exit(1)

        # We expect a dataset from the client
        recv = []
        while True:
            try:
                packet = client.recv(1024)
                if not packet:
                    break
                recv.append(packet)
            except Exception as e:
                print("Error receiving data from client: " + str(e))
                client.close()
                os._exit(1)
        # We already received all the information from the client
        client.close()

        clientPort, data = pickle.loads(b"".join(recv))

        print("Received the following data: " + str(data))

        # We process the data received and send it back to the client
        result = processData(data)
        print('Sending result: ' + str(result))
        sendResult(address[0], clientPort, result)

        # We tell the server we are available from now on
        if not msgServer("Yes"):
            os._exit(1)


def sendResult(addressIp, port, result):
    # We connect to the server to send back the result
    try:
        connectClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connectClient.connect((addressIp, port))
    except Exception as e:
        print("Error connection socket with client: " + str(e))
        connectClient.close()
        return

    # We send the result we got
    try:
        resultPickle = pickle.dumps([workerPort, result])
        connectClient.send(resultPickle)
    except Exception as e:
        print("Error sending result to client: " + str(e))


def meanData(ary):
    avg = 0
    t = 1
    for x in ary:
        avg += (x - avg) / t
        t += 1
    return avg


def processData(data):
    result = meanData(data)
    #In case you want to kill workers and see the fault tolerance
    #time.sleep(1)
    return [len(data), result]


# Creating a worker port to listen to client
workerPort = input("Introduce worker port number:\n")
workerPort = int(workerPort)

try:
    workerServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    workerServer.bind((host, workerPort))
    workerServer.listen()
except Exception as e:
    print("Error connection socket to listen to the client: " + str(e))
    workerServer.close()
    sys.exit(1)

# We tell the server we are ready
if not msgServer("Yes"):
    workerServer.close()
    sys.exit(1)


# We ping the server from time to time so that it knows we are alive
pingThread = threading.Thread(target=pingServer)
pingThread.start()

# We start a thread to handle the data sent from the client
handleDataThread = threading.Thread(target=handleDataFromClient)
handleDataThread.start()

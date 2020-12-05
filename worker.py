import threading
import socket
import time
import pickle
from include import *

host = '127.0.0.1'
serverPort = SERVER_PORT_WORKERS
clientPort = CLIENT_PORT

result = None
#TODO: LET THEM DO THE MEAN CALLING EACH OTHER. DO IT THINKING... DONT LET WORKERS INTERACT WITH EACH OTHER IN A CRAZY WAY. MAYBE COMMUNICATE WITH SERVER TO FIND WORKER WILLING TO DO THE MEAN

def pingServer():
    while True:
        try:
            msgServer("PING")
            time.sleep(PING_SLEEP)
        except:
            break

def msgServer(msg):
    try:
        dumpMsg = pickle.dumps([msg,workerPort])
        # Connecting to server port
        connectServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connectServer.connect((host, serverPort))
        connectServer.send(dumpMsg)
        connectServer.close()
    except:
        print("An error occurred when sending msg to server!")
        connectServer.close()

def handleDataFromClient():
    while True:
        client,address = workerServer.accept()
        msgServer("No")
        try:
            data = client.recv(1024)
            y = pickle.loads(data)
            print(y)
            result = processData(y)
            msgServer("Yes")
        except:
            print('Client has left')
            client.close()
            break

###TODO Not sure why it is not sending the result to the client

def sendResult(result):
    while result !=None:
        try:
            connectClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connectClient.connect((host, clientPort))
            result_pickle = pickle.dumps(result)
            connectClient.send(result_pickle)
            connectClient.close()
            result = None
        except:
            print("An error occurred when sending result to client!")
            connectClient.close()

def processData(data):
    result = sum(data)
    return data


# Creating a worker port to listen to client and possibly with each other?
workerPort = input("Introduce worker port number:\n")
workerPort = int(workerPort)
workerServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
workerServer.bind((host,workerPort))
workerServer.listen()

msgServer("Yes")
pingThread = threading.Thread(target = pingServer)
pingThread.start()
handleDataThread = threading.Thread(target = handleDataFromClient)
handleDataThread.start()
resultThread = threading.Thread(target = sendResult, args = (result,))
resultThread.start()
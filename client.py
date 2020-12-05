import pandas as pd
import socket
import pickle
import numpy as np
import threading
from sklearn import datasets
from include import *


#dataset = datasets.load_iris() #We'll work with the iris dataset --> we can change later if not suitable
dataset = np.arange(9.0)
host = '127.0.0.1'
serverPort = SERVER_PORT_CLIENTS
clientPort = CLIENT_PORT
workersJob = {}
jobsToGetDone = None

def startConnectionToServer():
        #Connecting to server port
        global connectServer
        global result
        connectServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connectServer.connect((host, serverPort))

        #We initialize the result to None
        result = None

        nbNodes = 3
        #Send how many nodes the client needs to the server
        msg = 'Send ' + str(nbNodes)  #TODO : agree on one message. what is this TODO???
        connectServer.send(msg.encode('ascii'))
        print('Asked for ' + str(nbNodes) + ' nodes')

        #We wait for the server to tell us how many workers it gives us and split the data accordingly
        nbNodesPickle = connectServer.recv(1024)
        nbNodes = pickle.loads(nbNodesPickle)
        print('Permission for ' + str(int(nbNodes)) + ' nodes')
        datasets = splitDataset(int(nbNodes)) #list of split datasets

        #We iniciate the thread listening for results.
        listenThread = threading.Thread(target = listenResult, args=(nbNodes,))
        listenThread.start()


        #List of numbers of jobs left to be done in inverse order to pop them in order
        jobsToGetDone = list(range(int(nbNodes)-1,-1,-1))
        #### First part : get list of IP @and ports of nodes and send the splitted data accordingly to the working nodes

        while(result == None): #while we don't have the number of nodes we asked for
            data = []

            try:
                data = connectServer.recv(1024) 
            except:
                #This is in case the socket is closed
                pass

            if(result == None and len(data) != 0):

                flag, addrs = pickle.loads(data) #@ ips and ports of working nodes sent by the server
                print(jobsToGetDone)
                #TODO: Remove prints
                #print(flag)
                #print(addrs)

                if flag == NEW_WORKERS: #We send data to these new workers
                    for i in range(len(addrs)):
                        workerIp = addrs[i][0]
                        workerPort = addrs[i][1]

                        jobNumber = jobsToGetDone.pop()
                        sendDataToWorker(datasets[jobNumber],workerIp,workerPort)

                        #We add to workersJob what job is this worker going to do
                        workersJob[(workerIp,workerPort)] = jobNumber

                elif flag == DEAD_WORKERS: #These workers are dead
                    #we decrease the number of the "good" nodes that way we know that the server is going to send another worker
                    for i in range(len(addrs)):
                        workerIp = addrs[i][0]
                        workerPort = addrs[i][1]

                        #Recover what data needs to be computed again because its worker die
                        jobNumber = workersJob[(workerIp,workerPort)] 
                        jobsToGetDone.append(jobNumber)

                #### Second part : get the computation result and see if check that it's correct
                #TODO : get the result of the computation from the workers and mark finished as correct. 
                #The program wont finish until he receives the result into the socket in the listenThread. If it receives it will close gently I thinkl


def sendDataToWorker(df,workerIp,workerPort):
    try:
        #Connect to the worker node
        workerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        workerSocket.connect((workerIp,workerPort))
        #Serialize the dataset with pickle
        df_pickled = pickle.dumps([clientPort,df])


        #send the serialized dataset with pickle
        workerSocket.send(df_pickled)

        #close the connection with the worker
        workerSocket.close()

    except:
        print("An error occurred when sending data to worker!")
        workerSocket.close()


def splitDataset(nbNodes):
    # split the dataset depending on how many working nodes we have
    #output : list of the datasets
    try:
        splitDf = np.array_split(dataset, nbNodes)
    except:
        print('Error splitting the data')
    return splitDf

### TODO Listening to the result from worker
def listenResult(nbNodes):
    global connectServer
    global result
    global clientPort
    partialResult = 0
    numberResultsReceived = 0

    clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    clientSocket.bind((host,clientPort))
    clientSocket.listen()
    while True:
        workerSocket,address = clientSocket.accept()
        #try:
        data = workerSocket.recv(1024)
        workerPort,data = pickle.loads(data)
        ### TODO accepting the intermediate result
        partialResult += data
        print("I received the result (" + str(data) + ") from data partition: " + str(workersJob[(address[0],workerPort)]))
        numberResultsReceived += 1
        if(numberResultsReceived == nbNodes):
            result = partialResult/nbNodes

            #We close both sockets letting connectServer socket to get out of the recv blocking call when all data is processed
            clientSocket.close()
            connectServer.shutdown(socket.SHUT_RDWR)
            connectServer.close()
            print("The result of the mean asked is: " + str(result))
            break
            
        #except:
         #   print('Error receiving result')
          #  clientSocket.close()
           # break

print("Starting the client connection ...")

#We ask for the client port to be used
clientPort = input("Introduce client port number:\n")
clientPort = int(clientPort)

startConnectionToServer()

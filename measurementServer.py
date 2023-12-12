import zmq
import threading
from taggerstuff import measurement
import json
import pandas as pd
import yaml
import numpy as np


class Server():
    def __init__(self, port, n_workers=4):
        self.port = str(port)
        url_worker = "inproc://workers"
        url_client = 'tcp://*:'+self.port
        self.context = zmq.Context.instance()
        # Socket to talk to clients
        clients = self.context.socket(zmq.ROUTER)
        clients.bind(url_client)
        self.initTagger()
        workers = self.context.socket(zmq.DEALER)
        workers.bind(url_worker)

        #SET TEST SIGNAL
        #self.m.startTestSignal()

        self.workers = []
        for k in range(0, n_workers):
            self.workers.append(threading.Thread(target=self.start_worker, daemon=True, args=(url_worker,k,)))
            self.workers[-1].start()

        zmq.proxy(clients, workers)
        # We never get here but clean up anyhow
        clients.close()
        workers.close()
        context.term()


    def start_worker(self, url_worker, k=0):
        """Worker routine"""
        context = self.context or zmq.Context.instance()
        # Socket to talk to dispatcher
        socket = context.socket(zmq.REP)
        socket.connect(url_worker)

        while True:
            message = socket.recv()
            message = message.decode()
            response = self.handle(message)
            # print('worker '+str(k)+' reporting for duty, '+response.decode())
            socket.send(response)

    def initTagger(self,filename="taggerconfig.yaml"):
        fp = open(filename, "r")
        paramsgen = yaml.load_all(fp,Loader=yaml.Loader)
        self.params = {}
        for g in paramsgen:
            for key in g:
                self.params[key] = g[key]
        self.m = measurement(self.params)

    def handle(self, message):
        print(message)
        response = "invalid"
        if message == "p?":
            response = json.dumps(self.params)
        elif message[:2] == "p.":
            body = message[2:]
            newParams = json.loads(body)
            print("Recieved updated parameters " + str(newParams))
            self.m.setParams(newParams)
        elif message[:2] == "m.":
            body = message[2:]
            if body == "correlation":
                data = self.m.measureCorrelation()
                bins = self.m.getCorrelationBins()
                df = pd.DataFrame({"Counts":data,"Bins":bins})
                response = df.to_json()
                if len(data)==1:
                    response = "-1"
                print(response)

            elif body == "12countrate":
                data = self.m.measure12countRate()
                print(data)
                self.m.reset12countRate()
                df = pd.DataFrame({"1":[data[0]],"2":[data[1]]})
                response = df.to_json()
                if len(data) == 1:
                    response = "-1"
                
        elif message == "correlation?":
            try:
                if self.measuringCorrelation == True:
                    response = "1"
                else:
                    response = "0"
            except:
                response = "0"
        elif message == "stopcorrelation":
            self.measuringCorrelation = False
            self.m.stopCorrelation()
            self.m.stop12countRate()
            response = "ok"
        elif message == "startcorrelation":
            self.measuringCorrelation = True
            self.m.startCorrelation()
            self.m.start12countRate()
            response="ok"


        return response.encode()

    
if __name__ == '__main__':
    zmqs = Server('5555', n_workers=4)

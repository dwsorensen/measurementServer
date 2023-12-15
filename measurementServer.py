import zmq
import threading
import TimeTagger
import json
import pandas as pd
import yaml
import numpy as np

class Server():
    def __init__(self, port, n_workers=4):
        self.maxid = 0
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

    
    def initTagger(self,filename="taggerconfig.yaml"):
        fp = open(filename, "r")
        paramsgen = yaml.load_all(fp,Loader=yaml.Loader)
        self.taggerparams = {}
        for g in paramsgen:
            for key in g:
                self.taggerparams[key] = g[key]
        self.tagger = TimeTagger.createTimeTagger()
        self.tagger.setTriggerLevel(1,self.taggerparams["trigger_1"])
        self.tagger.setTriggerLevel(2,self.taggerparams["trigger_2"])
        self.tagger.setTriggerLevel(3,self.taggerparams["trigger_3"])
        self.tagger.setEventDivider(3,self.taggerparams["eventdivider_3"])
        self.tagger.setDeadtime(1,self.taggerparams["deadtime_1"])
        self.tagger.setDeadtime(2,self.taggerparams["deadtime_2"])

        self.taggerProxies = {}
        self.measurementServices = {}
        self.synchronizers = {}

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

    def handle(self, message):
        message = json.loads(message)
        print(message)
        response = "invalid"
        
        request = message["request"]

        match request:
            case "init":
                measurement = message["measurement"]
                params = message["params"]
                match measurement:
                    case "correlationstream":
                        synchronized = TimeTagger.SynchronizedMeasurements(self.tagger)
                        syncProxy = synchronized.getTagger()
                        measurements = {}
                        cChannel1 = int(params["correlation_channel1"])
                        cChannel2 = int(params["correlation_channel2"])
                        binWidth = int(params["correlation_binwidth"])
                        nBins = int(params["correlation_nbins"])
                        measurements["correlation"] = TimeTagger.Correlation(syncProxy,cChannel1,cChannel2,binWidth,nBins)
                        measurements["countrate"] = TimeTagger.Countrate(syncProxy,[1,2])
                        newid = self.maxid
                        self.maxid = self.maxid + 1
                        self.measurementServices[newid] = measurements
                        self.taggerProxies[newid] = syncProxy
                        self.synchronizers[newid] = synchronized
                        response = str(newid)

            case "start":
                id = int(message["id"])
                self.synchronizers[id].start()     
            
            case "stop":
                id = int(message["id"])
                self.synchronizers[id].start() 

            case "clear":
                id = int(message["id"])
                measurements = self.measurementServices[id]
                for key in measurements:
                    measurements[key].clear()

            case "data":
                id = int(message["id"])
                key = message["key"]
                measurement = self.measurementServices[id][key]
                data = measurement.getData()
                match key:
                    case "correlation":
                        config = measurement.getConfiguration()["params"]
                        print(config)
                        binWidth = config["binwidth"]
                        nBins = config["n bins"]
                        r = binWidth * nBins
                        bins = np.linspace(-1*r,r,nBins)
                        data = {
                            "bins":bins,
                            "counts":data
                        }
                        df = pd.DataFrame(data)
                        response = df.to_json()
                    case "countrate":
                        data = {
                            "channel1":[data[0]],
                            "channel2":[data[1]]
                        }
                        df = pd.DataFrame(data)
                        response = df.to_json()

        response = response.encode()
        return response

    
if __name__ == '__main__':
    try:
        zmqs = Server('5555', n_workers=4)
    except KeyboardInterrupt:
        print("Bye-bye :(")

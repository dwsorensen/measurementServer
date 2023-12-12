import TimeTagger
import numpy as np

class measurement:
    def __init__(self, params = -1):
        self.tagger = TimeTagger.createTimeTagger()
        self.params = self.defaultParams()
        self.setParams(params)
        self.updateTaggerSettings()
        
    def defaultParams(self):
        default = {
            "start_channel": 3,
            "stop_channel_1": 1,
            "stop_channel_2": 2,
            "binwidth_1": 10000,
            "binwidth_2": 10000,
            "n_bins_1": 10,
            "n_bins_2": 10,
            "trigger_1": 0.02,
            "trigger_2": 0.02,
            "trigger_3":0.1,
            "deadtime_1":50000,
            "deadtime_2":50000,
            "eventdivider_3":10
        }
        return default
    
    def setParams(self,params):
        if params != -1:
            for key in params:
                self.params[key] = params[key]

    def updateTaggerSettings(self,params=-1):
        self.setParams(params)
        for key in self.params:
            if key[0:7] == "trigger":
                channel = int(key[8])
                self.tagger.setTriggerLevel(channel,self.params[key])
            elif key[0:8] == "deadtime":
                channel = int(key[9])
                self.tagger.setDeadtime(channel,self.params[key])
            elif key[0:12] == "eventdivider":
                channel = int(key[13])
                self.tagger.setEventDivider(channel,self.params[key])
            
    def startHistogram2D(self,params=-1):
        self.setParams(params)
        self.updateTaggerSettings()
        self.hist2d = TimeTagger.Histogram2D(self.tagger, self.params["hist2d_start_channel"],self.params["hist2d_stop_channel_1"],self.params["hist2d_stop_channel_2"],self.params["hist2d_binwidth_1"],self.params["hist2d_binwidth_2"],self.params["n_bins_1"],self.params["hist2d_n_bins_2"])

    def startCorrelation(self, params=-1):
        self.setParams(params)
        self.updateTaggerSettings()
        self.correlation = TimeTagger.Correlation(self.tagger,int(self.params["correlation_channel1"]),int(self.params["correlation_channel2"]),int(self.params["correlation_binwidth"]),int(self.params["correlation_nbins"]))
        
    def stopCorrelation(self):
        try:
            self.correlation.stop()
        except:
            pass

    def measureHistogram2D(self):
        data = self.hist2d.getData()
        return data
    
    def measureCorrelation(self):
        try:
            data = self.correlation.getData()
        except AttributeError:
            data = -1
        return data
    
    def getCorrelationBins(self):
        binWidth = int(self.params["correlation_binwidth"])
        nBins = int(self.params["correlation_nbins"])
        bins = np.linspace(0,nBins*binWidth,nBins)
        shift = np.full(np.shape(bins),binWidth*nBins/2)
        bins = bins - shift
        return bins

    def getHistogram2DBins(self):
        n1 = self.params["n_bins_1"]
        n2 = self.params["n_bins_2"]
        w1 = self.params["binwidth_1"]
        w2 = self.params["binwidth_2"]
        bins1 = np.arange(0,n1*w1,w1)
        bins2 = np.arange(0,n2*w2,w2)
        return (bins1,bins2)
    
    def startTestSignal(self):
        self.tagger.setTestSignal(1,True)
        self.tagger.setTestSignal(2,True)

    def stopTestSignal(self):
        self.tagger.setTestSignal(1,False)
        self.tagger.setTestSignal(2,False)

    def start12countRate(self):
        self.countrate = TimeTagger.Countrate(self.tagger,[1,2])

    def measure12countRate(self):
        try:
            data = self.countrate.getData()
        except AttributeError:
            data = -1
        return data
    
    def reset12countRate(self):
        self.countrate.clear()

    def stop12countRate(self):
        self.countrate.stop()
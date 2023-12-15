import streamlit as st
from client import Client
import json
import numpy as np
import time
import pandas as pd
import plotly.express as px
import io
import math
import yaml

ip = "128.138.222.132"
port = "5555"

ss = st.session_state 

def toggleMeasurement():
    global ss
    if ss.isMeasuring:
        message = {
            "request":"stop",
            "id":ss.sessionID
        }
        ss.isMeasuring = False
        ss.toggleLabel = "Start Measurement"
        messageJson = json.dumps(message)
        ss.c.send_message(messageJson)
    else:
        message = {
            "request":"start",
            "id":ss.sessionID
        }
        ss.isMeasuring = True
        ss.toggleLabel = "Stop Measurement"
        messageJson = json.dumps(message)
        ss.c.send_message(messageJson)
        time.sleep(0.5)

def loadParams(filename):
    fp = open(filename, "r")
    paramsgen = yaml.load_all(fp,Loader=yaml.Loader)
    params = {}
    for g in paramsgen:
        for key in g:
            params[key] = g[key]
    return params

def getCorrelationData():
    message = {
                "request":"data",
                "id":ss.sessionID,
                "key":"correlation"
            }
    messageJson = json.dumps(message)
    resp = ss.c.send_message(messageJson)
    df = pd.read_json(io.StringIO(resp))
    return df

def getCountrateData():
    message = {
                "request":"data",
                "id":ss.sessionID,
                "key":"countrate"
            }
    messageJson = json.dumps(message)
    resp = ss.c.send_message(messageJson)
    df = pd.read_json(io.StringIO(resp))
    return df
    
def updateElements():
    if ss.isMeasuring:
        ss.correlationData = getCorrelationData()
        ss.countrateData = getCountrateData()
        ss.data = True
    container = st.container()
    with container:
        if ss.data:
            fig = px.line(ss.correlationData,x="bins",y="counts")
            ss.lastFig = fig
            st.plotly_chart(fig)

            rate1 = ss.countrateData["channel1"][0]
            rate2 = ss.countrateData["channel2"][0]
            col1,col2 = st.columns(2)
            with col1:
                st.write("Channel 1 Countrate: %i"%int(rate1))
            with col2:
                st.write("Channel 2 Countrate: %i"%int(rate2))
    return container

def loadMeasurement():
    global ss
    ss.data = False
    ss.c = Client(ip, port)
    ss.updateRate = 0.5
    ss.params = loadParams("./config/1_config.yaml")
    messageDict = {
        "request":"init",
        "measurement":"correlationstream",
        "params":ss.params
    }
    messageJson = json.dumps(messageDict)
    ss.sessionID = ss.c.send_message(messageJson)
    ss.toggleLabel = "Start Measurement"
    ss.isMeasuring = False
    print("Recieved ID " + str(ss.sessionID))
    ss.isLoaded = True

def clearMeasurement():
    message = {
        "request":"clear",
        "id":ss.sessionID
    }
    messageJson = json.dumps(message)
    ss.c.send_message(messageJson)
    ss.data = False
    time.sleep(0.5)
#Load. Just display load button if it isn't loaded.
try:
    ss.isLoaded
except AttributeError:
    c = st.button("Load",on_click = loadMeasurement)
    st.write("In order to ensure that Streamlit doesn't send a ton of requests of the server for every load, you are required to manually click the load button above.")
else:
    #Live elements of the page
    liveElement = st.empty()

    #Control buttons
    with st.container():
        col1,col2 = st.columns(2)
        with col1:
            start = st.button(ss.toggleLabel,on_click = toggleMeasurement)
        with col2:
            clear = st.button("Clear",on_click=clearMeasurement)

    #Histogram settings
    with st.expander("Histogram Settings:"):
            with st.form("histSettings"):
                updateRate = st.text_input("Update Time (s)",value=str(ss.updateRate))
                ch1 = st.text_input("Channel 1", value=str(ss.params["correlation_channel1"]))
                ch2 = st.text_input("Channel 2", value=str(ss.params["correlation_channel2"]))
                binwidth = st.text_input("Bin Width", value=str(ss.params["correlation_binwidth"]))
                nbins = st.text_input("N Bins", value=str(ss.params["correlation_nbins"]))
                histSubmit = st.form_submit_button("Submit")
                if histSubmit:
                    newParams = {
                        "correlation_channel1":int(ch1),
                        "correlation_channel2":int(ch2),
                        "correlation_binwidth":int(binwidth),
                        "correlation_nbins":int(nbins)
                    }
                    ss.updateRate = float(updateRate)
                    message = {
                        "request":"params",
                        "params":newParams
                    }
                    messageJson = json.dumps(message)
                    ss.c.send_message(messageJson)
                    st.write("Settings update not quite supported yet.")
                    print("Submitted " + str(newParams))


    #Update plot!
    with liveElement:
        while True:
            tStart = time.time()
            updateElements()
            tStop = time.time()
            deltaT = tStop - tStart
            if deltaT < ss.updateRate:
                time.sleep(ss.updateRate - deltaT)
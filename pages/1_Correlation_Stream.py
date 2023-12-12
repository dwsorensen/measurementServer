import streamlit as st
from client import Client
import json
import numpy as np
import time
import pandas as pd
import plotly.express as px
import io
import math

ip = "128.138.222.132"
port = "5555"

ss = st.session_state 

def toggleMeasurement():
    global ss
    if ss.isMeasuring:
        ss.c.send_message("stopcorrelation")
        ss.isMeasuring = False
        if type(ss.plotDF) == int:
            ss.toggleLabel = "Start Measurement"
        else:
            ss.toggleLabel = "Restart Measurement"
    else:
        ss.c.send_message("startcorrelation")
        ss.isMeasuring = True
        ss.toggleLabel = "Stop Measurement"

def getCorrelationData():
    global ss
    resp = ss.c.send_message("m.correlation")
    df = pd.read_json(io.StringIO(resp))
    return df

def getCountRateData():
    global ss
    resp = ss.c.send_message("m.12countrate")
    df = pd.read_json(io.StringIO(resp))
    return df

def updateElements():
    container = st.container()
    with container:
        if ss.isMeasuring:
            ss.plotDF = getCorrelationData()
            countRates = getCountRateData()
            ss.rate1 = countRates[1][0]
            ss.rate2 = countRates[2][0]
        if type(ss.plotDF) != int:
            fig = px.line(ss.plotDF,x="Bins",y="Counts")
            st.plotly_chart(fig)
        try:
            if not(math.isnan(ss.rate1) or math.isnan(ss.rate2)):
                col1,col2 = st.columns(2)
                with col1:
                    st.write("Channel 1 Countrate: %i"%int(ss.rate1))
                with col2:
                    st.write("Channel 2 Countrate: %i"%int(ss.rate2))
        except NameError:
            pass
    return container
#Load
try:
    ss.isLoaded
except AttributeError:
    print("Loading")
    ss.c = Client(ip, port)
    ss.updateRate = 0.5
    ss.plotDF = -1
    jsonparams = ss.c.send_message("p?")
    ss.params = json.loads(jsonparams)
    isMeasuring = ss.c.send_message("correlation?")
    print("Is measuring: " + isMeasuring)
    if isMeasuring == "1":
        ss.isMeasuring = True
        ss.toggleLabel = "Stop Measurement"
    else:
        ss.isMeasuring = False
        ss.toggleLabel = "Start Measurement"
    ss.isLoaded = True

#Plot
liveElement = st.empty()

#Control buttons
with st.container():
    b = st.button(ss.toggleLabel,on_click = toggleMeasurement)

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
                ss.c.send_message("p." + json.dumps(newParams))
                print("Submitted " + str(newParams))

#Timetagger settings
with st.expander("Timetagger Settings"):
    with st.form("timetaggerSettings"):
        trigger1 = st.text_input("Trigger Level (Channel 1)",value=str(ss.params["trigger_1"]))
        trigger2 = st.text_input("Trigger Level (Channel 2)",value=str(ss.params["trigger_2"]))
        trigger3 = st.text_input("Trigger Level (Channel 3)",value=str(ss.params["trigger_3"]))

        deadtime1 = st.text_input("Dead time (Channel 1)",value=str(ss.params["deadtime_1"]))
        deadtime2 = st.text_input("Dead time (Channel 2)",value=str(ss.params["deadtime_2"]))
        eventdivider3 = st.text_input("Clock Downsample Factor",value=str(ss.params["eventdivider_3"]))
        submitButton = st.form_submit_button("Update")
        if submitButton:
            newParams = {
                "deadtime_1":int(deadtime1),
                "deadtime_2":int(deadtime2),
                "eventdivier_3":int(eventdivider3),
                "trigger_1":float(trigger1),
                "trigger_2":float(trigger2),
                "trigger_3":float(trigger3)
            }
            ss.c.send_message("p." + json.dumps(newParams))
            print("Submitted " + str(newParams))

#Update plot!
with liveElement:
    while True:
        tStart = time.time()
        c = updateElements()
        tStop = time.time()
        deltaT = tStop - tStart
        if deltaT < ss.updateRate:
            time.sleep(ss.updateRate - deltaT)



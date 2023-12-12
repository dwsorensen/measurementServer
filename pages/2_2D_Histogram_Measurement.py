import streamlit as st
from client import Client
import json

st.title("Coming soon :)")
"""
ip = "128.138.222.132"
port = "5555"

c = Client(ip, port)
jsonparams = c.send_message("p?")
params = json.loads(jsonparams)

plotC = st.container()
paramsC = st.expander("Parameters")
controlC = st.container()

with plotC:
    st.write("This is where the histogram will go")

with paramsC.form("Timetagger Parameters"):
    col1, col2, col3 = st.columns(3)
    with col1:
        startChannel = st.text_input("Start Channel", value=str(params["start_channel"]))
        stopChannel1 = st.text_input("Stop Channel 1", value=str(params["stop_channel_1"]))
        stopChannel2 = st.text_input("Stop Channel 2", value=str(params["stop_channel_2"]))
    with col2:
        binWidth1 = st.text_input("Bin Width (1)", value=str(params["binwidth_1"]))
        nBins1 = st.text_input("N Bins (1)", value=str(params["n_bins_1"]))
        binWidth2 = st.text_input("Bin Width (2)", value=str(params["binwidth_2"]))
        nBins2 = st.text_input("N Bins (2)", value=str(params["n_bins_2"]))
    with col3:
        deadtime1 = st.text_input("Dead time (Channel 1)",value=str(params["deadtime_1"]))
        deadtime2 = st.text_input("Dead time (Channel 2)",value=str(params["deadtime_2"]))
        eventdivider3 = st.text_input("Clock Downsample Factor",value=str(params["eventdivider_3"]))
    submitButton = st.form_submit_button("Update")

with controlC:
    st.button("Start Measurement")
"""
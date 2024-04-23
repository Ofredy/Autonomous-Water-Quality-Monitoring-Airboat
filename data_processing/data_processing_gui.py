import os
import glob

# Libary imports
import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import matplotlib.pyplot as plt 
from matplotlib.legend_handler import HandlerPathCollection

# Our imports
from plotting import *
from anomaly_detection import *


# System constants
graphs = ['gps_graph', 'time_vs_anomaly_score', 'time_vs_ph', 'time_vs_turbidity', 'time_vs_temp', 'time_vs_tds']
normal_ranges = {
    'PH': (5, 8.5),
    'Temperature': (65, 75),
    'TDS': (150, 300),
    'Turbidity': (0, 10),
}

class DataProcessingGUI:
    def __init__(self):
        self.graph_objs = {}
        self.graphs_generated = False
        self.uploaded_file = None


    def _generate_graphs(self):
        if self.uploaded_file is None:
            return

        
        # Convert the uploaded file to a DataFrame
        df = pd.read_csv(self.uploaded_file)

        # Apply anomaly detection and plotting
        
        deck = plot_data(df)  

        self.graph_objs['3D Anomaly Visualization'] = deck
        self.graphs_generated = True

    def _display_graph(self):
        if not self.graphs_generated:
            return

        for graph_name, graph_obj in self.graph_objs.items():
            st.markdown(f"<p style='font-family:sans-serif; font-size: 20px; text-align:center;'>{graph_name}</p>", unsafe_allow_html=True)
            st.pydeck_chart(graph_obj)

    def window(self):
        st.set_page_config(page_title="Airboat PMDT")

        with st.container():
            st.markdown('<p style="font-family:sans-serif; font-size: 36px;">Airboat Post Mission Data Processing Tool</p>', unsafe_allow_html=True)

            # File uploader widget
            self.uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

            if self.uploaded_file is not None:
                self._generate_graphs()

        with st.container():
            if self.graphs_generated:
                self._display_graph()

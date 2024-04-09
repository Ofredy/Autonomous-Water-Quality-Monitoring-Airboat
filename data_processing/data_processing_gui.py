import os
import glob

# Libary imports
import streamlit as st
import pandas as pd
import pydeck as pdk
# Our imports
from loclal_pydeck import *
from local_outlier import *


# System constants
graphs = ['gps_graph', 'time_vs_anomaly_score', 'time_vs_ph', 'time_vs_turbidity', 'time_vs_temp', 'time_vs_tds']
data = {
    'Time': time,
    'GPS_Latitude': gps_lat,
    'GPS_Longitude': gps_long,
    'PH': ph,
    'Turbidity': turbidity,
    'Temperature': temp,
    'TDS': tds,
}
class DataProcessingGUI:
    def __init__(self):
        self.graph_objs = {}
        self.graphs_generated = False
        self.uploaded_file = None

    @staticmethod
    def compute_color(anomaly_score):
        if anomaly_score > 0.5:
            return [255, 0, 0, 160]  # Red color for higher anomaly scores
        else:
            return [0, 0, 255, 160]  # Blue color for lower anomaly scores

    def _perform_anomaly_detection(self, df):
        dt['Anomaly_Score'] = dt[['PH_Score', 'Temp_Score', 'TDS_Score', 'Turbidity_Score']].mean(axis=1)
        df['color'] = dt['Anomaly_Score'].apply(self.compute_color)
        return df

    def _generate_graphs(self):
        if self.uploaded_file is None:
            return

        # Load the uploaded CSV file into a DataFrame
        df = pd.read_csv(self.uploaded_file)
      
        df = self._perform_anomaly_detection(df)
        
        # Define tooltip for hovering
        tooltip = {
            "html": "<b>Time:</b> {Time}<br>" +
                    "<b>Longitude:</b> {Longitude}<br>" +
                    "<b>Latitude:</b> {Latitude}<br>" +
                    "<b>PH:</b> {PH}<br>" +
                    "<b>Temperature:</b> {Temperature}<br>" +
                    "<b>TDS Score:</b> {TDS}<br>" +
                    "<b>Turbidity:</b> {Turbidity}",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white"
            }
        }

    

           # Create a pydeck layer for the data
        scatterplot_layer = pdk.Layer(
        'ColumnLayer',
        df,
        get_position=['Longitude', 'Latitude'],
        get_color='color',
        auto_highlight=True,
        elevation_scale=50,
        get_radius = 200,
        pickable=True,
        elevation_range=[0, 3000],
        extruded=True,                 
        coverage=4  # Adjust multiplier as needed to visualize anomaly score elevation
        )

        invisible_layer = pdk.Layer(
        'ColumnLayer',
        df,
        get_position=['Longitude', 'Latitude'],
        get_color=[0,0,0,0],
        auto_highlight=True,
        elevation_scale=50,
        get_radius = 300,
        pickable=True,
        elevation_range=[0, 3000],
        extruded=True,                 
        coverage=1  # Adjust multiplier as needed to visualize anomaly score elevation
        )

            # Adjust latitude, longitude, and zoom according to your data's location
        INITIAL_VIEW_STATE = pdk.ViewState(
        latitude=df["Latitude"].mean(),
        longitude=df["Longitude"].mean(),
        zoom=5,
        min_zoom=5,
        max_zoom=15,
        pitch=40.5,
        bearing=-27.36)

        # Create the deck
        deck = pdk.Deck(
        layers=[invisible_layer,scatterplot_layer],
        initial_view_state=INITIAL_VIEW_STATE,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v9",
        )
        
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



# System imports
import os
import glob

# Libary imports
import streamlit as st

# Our imports


# System constants
graphs = ['gps_graph', 'time_vs_anomaly_score', 'time_vs_ph', 'time_vs_turbidity', 'time_vs_temp', 'time_vs_tds']


class DataProcessingGUI:

    def __init__(self):
    
        self.graph_objs = {}
        self.graphs_generated = False

    def _generate_graphs(self):
        
        if len(self.data_csv) == 0:
            return

        ############## GUI CODE NEEDS TO CONNECT TO ANOMALY DETECTION & PLOTTING HERE TO PLOT ##############


        self.graphs_generated = True

    def _display_graph(self):

        if len(self.selected_graph) == 0:
            return
        
        for idx, graph in enumerate(graphs):

            if graph in self.graph_objs.keys() and idx == 0:

                gps_graph_label = f"<p style='font-family:sans-serif; font-size: 20px; text-align:center;'>{graph}</p>"
                st.markdown(gps_graph_label, unsafe_allow_html=True)
                st.pydeck_chart(self.graph_objs[graph])
            
            elif graph in self.graph_objs.keys():

                graph_label = f"<p style='font-family:sans-serif; font-size: 20px; text-align:center;'>{graph}</p>"
                st.markdown(graph_label, unsafe_allow_html=True)
                st.pyplot(self.graph_objs[graph])

    def window(self):
        
        st.set_page_config(page_title="Airboat PMDT")

        with st.container():
            
            title = '<p style="font-family:sans-serif; font-size: 36px;">Airboat Post Mission Data Processing Tool</p>'
            st.markdown(title, unsafe_allow_html=True)

            self.data_csv = st.multiselect("Select a data csv file to visualize", glob.glob(os.path.join('data', '*.csv')), max_selections=1)

            self._generate_graphs()

        with st.container():

            if self.graphs_generated:

                self.selected_graph = st.multiselect("Select graphs to inspect", graphs)

                self._display_graph()

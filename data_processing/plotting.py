import pydeck as pdk
import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from anomaly_detection import *
import matplotlib.pyplot as plt 
from matplotlib.legend_handler import HandlerPathCollection
normal_ranges = {
    'PH': (5, 8.5),
    'Temperature': (65, 75),
    'TDS': (150, 300),
    'Turbidity': (0, 10),
}
feature_columns = ['PH', 'Temperature', 'TDS', 'Turbidity']

## Example adjustment for color computation
def compute_color(row):
    # Check individual anomaly flags for sensors. If any flag is set, color the point as an anomaly.
    if row['ph_anomaly_flag'] == 1 or row['temp_anomaly_flag'] == 1 or \
       row['tds_anomaly_flag'] == 1 or row['turbidity_anomaly_flag'] == 1:
        return [255, 0, 0, 160]  # Red for any sensor anomaly
    else:
        return [0, 0, 255, 160]  # Blue for normal
def add_jitter(df, std=0.0001):
    # Add random noise within a specified standard deviation
    df['Longitude'] += np.random.normal(0, std, size=len(df))
    df['Latitude'] += np.random.normal(0, std, size=len(df))
    return df
def plot_data(df):
    

    
    # Perform anomaly detection on the sensor columns
    df = anomaly_detections(df)
    df = add_jitter(df)  # Apply jitter to coordinates
    #df['Anomaly_Score'] = df[['norm_ph_scores', 'norm_temp_scores', 'norm_tds_scores', 'norm_turbidity_scores']].mean(axis=1)

    # Apply the function to the 'Anomaly_Score' column to create the 'color' column
    df['color'] = df.apply(compute_color, axis=1)
    


    tooltip = {
            "html": "<b>Time:</b> {Time}<br>" +
                    "<b>Longitude:</b> {Longitude}<br>" +
                    "<b>Latitude:</b> {Latitude}<br>" +
                    "<b>PH:</b> {PH}<br>" +
                    "<b>PH_Flag:</b> {ph_anomaly_flag}<br>" +
                    "<b>Temperature:</b> {Temperature}<br>" +
                    "<b>Temp_Flag:</b> {temp_anomaly_flag}<br>" +
                    "<b>TDS:</b> {TDS}<br>" +
                    "<b>TDS_Flag:</b> {tds_anomaly_flag}<br>" +
                    "<b>Turbidity:</b> {Turbidity}<br>"+
                    "<b>Turbidity_Flag:</b> {turbidity_anomaly_flag}<br>",
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
    elevation_scale=2,
    get_radius = 0.1,
    pickable=True,
    elevation_range=[0, 4],
    extruded=True,                 
    coverage=0.03  # Adjust multiplier as needed to visualize anomaly score elevation
    )

    invisible_layer = pdk.Layer(
    'ColumnLayer',
    df,
    get_position=['Longitude', 'Latitude'],
    get_color=[0,0,0,0],
    auto_highlight=True,
    elevation_scale=10,
    get_radius = 500,
    pickable=True,
    elevation_range=[0, 500],
    extruded=True,                 
    coverage=4  # Adjust multiplier as needed to visualize anomaly score elevation
    )

    # Adjust latitude, longitude, and zoom according to your data's location
    INITIAL_VIEW_STATE = pdk.ViewState(
    latitude=df["Latitude"].mean(),
    longitude=df["Longitude"].mean(),
    zoom=11,
    min_zoom=5,
    max_zoom=15,
    pitch=20, # 0 gives a top-down view
    bearing=0) # Aligns with north at top

    # Create the deck
    deck = pdk.Deck(
    layers=[invisible_layer,scatterplot_layer],
    initial_view_state=INITIAL_VIEW_STATE,
    tooltip=tooltip,
     )
    return deck
    #deck.to_html('water_quality_anomalies.html', open_browser=True)

#file_path = 'water_quality_data.csv'
#plot_data(file_path)


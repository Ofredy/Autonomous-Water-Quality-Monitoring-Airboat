import pydeck as pdk
import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from fake_data import *
from local_outlier import *
import matplotlib.pyplot as plt 
from matplotlib.legend_handler import HandlerPathCollection


# Assuming gps_long, gps_lat, norm_ph_scores, norm_temp_scores, norm_tds_scores, norm_turbidity_scores are defined as in your code

# Combine GPS coordinates and normalized scores into a single DataFrame
data = {
    'Longitude': gps_long,
    'Latitude': gps_lat,
    'PH_Score': norm_ph_scores,
    'Temp_Score': norm_temp_scores,
    'TDS_Score': norm_tds_scores,
    'Turbidity_Score': norm_turbidity_scores,
}

df = pd.DataFrame(data)
df['Anomaly_Score'] = df[['PH_Score', 'Temp_Score', 'TDS_Score', 'Turbidity_Score']].mean(axis=1)
## Example adjustment for color computation
def compute_color(anomaly_score):
    if anomaly_score > 0.5:
        return [255, 0, 0, 160]  # Red color for higher anomaly scores
    else:
        return [0, 0, 255, 160]  # Blue color for lower anomaly scores

# Apply the function to the 'Anomaly_Score' column to create the 'color' column
df['color'] = df['Anomaly_Score'].apply(compute_color)


# Create a pydeck layer for the data
scatterplot_layer = pdk.Layer(
    'ColumnLayer',
    df,
    get_position=['Longitude', 'Latitude'],
    get_color='color',
    auto_highlight=True,
    elevation_scale=50,
    pickable=True,
    elevation_range=[0, 3000],
    extruded=True,                 
    coverage=1  # Adjust multiplier as needed to visualize anomaly score elevation
)

# Adjust latitude, longitude, and zoom according to data's location
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
    layers=[scatterplot_layer],
    initial_view_state=INITIAL_VIEW_STATE,
)

# To display the visualization outside of a Jupyter notebook, save it as an HTML file
deck.to_html('water_quality_anomalies.html', open_browser=True)

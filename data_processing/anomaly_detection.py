import numpy as np

from sklearn.preprocessing import MinMaxScaler
import pandas as pd

from sklearn.ensemble import IsolationForest

def anomaly_detections(df):
    
    feature_columns = ['PH', 'Turbidity', 'Temperature', 'TDS']
    # Create Isolation Forest models for each feature column
    iso_forest_ph = IsolationForest(n_estimators=50, max_samples='auto', contamination=float(0.01),max_features=1.0)
    iso_forest_turbidity = IsolationForest(n_estimators=50, max_samples='auto', contamination=float(0.01),max_features=1.0)
    iso_forest_temperature = IsolationForest(n_estimators=50, max_samples='auto', contamination=float(0.01),max_features=1.0)
    iso_forest_tds = IsolationForest(n_estimators=50, max_samples='auto', contamination=float(0.01),max_features=1.0)
    
    # Fit the models and predict anomalies
    iso_forest_ph.fit(df[['PH']])
    iso_forest_turbidity.fit(df[['Turbidity']])
    iso_forest_temperature.fit(df[['Temperature']])
    iso_forest_tds.fit(df[['TDS']])
    
    # Calculate the anomaly scores (the lower, the more abnormal)
    df['ph_scores'] = iso_forest_ph.decision_function(df[['PH']])
    df['turbidity_scores'] = iso_forest_turbidity.decision_function(df[['Turbidity']])
    df['temperature_scores'] = iso_forest_temperature.decision_function(df[['Temperature']])
    df['tds_scores'] = iso_forest_tds.decision_function(df[['TDS']])
    
    #predict the anomaly
    df['ph_anomaly'] = iso_forest_ph.predict(df[['PH']])
    df['turbidity_anomaly'] = iso_forest_turbidity.predict(df[['Turbidity']])
    df['temp_anomaly'] = iso_forest_temperature.predict(df[['Temperature']])
    df['tds_anomaly'] = iso_forest_tds.predict(df[['TDS']])
    
   
    # Change labels from -1, 1 to 1, 0
    #Easier to understand for user
    anomaly_columns = ['ph_anomaly', 'turbidity_anomaly', 'temp_anomaly', 'tds_anomaly']
    for col in anomaly_columns:
        df[col] = df[col].apply(lambda x: 1 if x == -1 else 0)
    
    return df


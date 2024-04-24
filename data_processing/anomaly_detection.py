import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

def anomaly_detections(df):
    feature_columns = ['PH', 'Turbidity', 'Temperature', 'TDS']
    


    # Set LOF parameters
    contamination = 0.01  # Lowered to reduce sensitivity
    n_neighbors = 20      # Increased to smooth anomaly detection
    anomaly_threshold = 0.998  # Higher threshold for anomaly flagging
    
    # Apply LOF for each feature separately
    clf_ph = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    clf_turbidity = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    clf_temperature = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    clf_tds = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    
    # Perform anomaly detection
    df['ph_pred'] = clf_ph.fit_predict(df[['PH']])
    df['turbidity_pred'] = clf_turbidity.fit_predict(df[['Turbidity']])
    df['temp_pred'] = clf_temperature.fit_predict(df[['Temperature']])
    df['tds_pred'] = clf_tds.fit_predict(df[['TDS']])
    
    # Calculate negative outlier factor scores
    df['ph_scores'] = clf_ph.negative_outlier_factor_
    df['turbidity_scores'] = clf_turbidity.negative_outlier_factor_
    df['temp_scores'] = clf_temperature.negative_outlier_factor_
    df['tds_scores'] = clf_tds.negative_outlier_factor_

    # Normalize scores and apply thresholds to set flags
    df['norm_ph_scores'] = (df['ph_scores'] - df['ph_scores'].min()) / (df['ph_scores'].max() - df['ph_scores'].min())
    df['norm_turbidity_scores'] = (df['turbidity_scores'] - df['turbidity_scores'].min()) / (df['turbidity_scores'].max() - df['turbidity_scores'].min())
    df['norm_temp_scores'] = (df['temp_scores'] - df['temp_scores'].min()) / (df['temp_scores'].max() - df['temp_scores'].min())
    df['norm_tds_scores'] = (df['tds_scores'] - df['tds_scores'].min()) / (df['tds_scores'].max() - df['tds_scores'].min())
    
    df['ph_anomaly_flag'] = df['norm_ph_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    df['turbidity_anomaly_flag'] = df['norm_turbidity_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    df['temp_anomaly_flag'] = df['norm_temp_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    df['tds_anomaly_flag'] = df['norm_tds_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)

    return df

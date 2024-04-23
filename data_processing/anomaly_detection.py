import numpy as np
from sklearn.neighbors import LocalOutlierFactor
import matplotlib.pyplot as plt 
from matplotlib.legend_handler import HandlerPathCollection
from sklearn.preprocessing import MinMaxScaler
import pandas as pd  # Make sure to import pandas
def anomaly_detections(df):
    feature_columns = ['PH', 'Turbidity', 'Temperature', 'TDS']
    # Reshape data for LOF
    X = df[feature_columns[0]].values.reshape(-1, 1)
    Y = df[feature_columns[1]].values.reshape(-1, 1)
    Z = df[feature_columns[2]].values.reshape(-1, 1)
    A = df[feature_columns[3]].values.reshape(-1, 1)
    # Create a new LocalOutlierFactor instance for each parameter
    clf_ph = LocalOutlierFactor(n_neighbors=20, contamination=0.01)
    clf_temp = LocalOutlierFactor(n_neighbors=20, contamination=0.01)
    clf_tds = LocalOutlierFactor(n_neighbors=20, contamination=0.01)
    clf_turbidity = LocalOutlierFactor(n_neighbors=20, contamination=0.01)

    df['ph_pred'] = clf_ph.fit_predict(X)
    df['turbidity_pred'] = clf_temp.fit_predict(Y)
    df['temp_pred'] = clf_tds.fit_predict(Z)
    df['tds_pred'] = clf_turbidity.fit_predict(A)


    #df['ph_errors'] = (ph_pred != ground_truth_ph).sum()
    #df['temp_errors'] = (temp_pred != ground_truth_temp).sum()
    #df['tds_errors'] = (tds_pred != ground_truth_tds).sum()
    #df['turbidity_errors'] = (turbidity_pred != ground_truth_turbidity).sum()

    # Calculate the negative outlier factor scores for each parameter
    df['ph_scores'] = clf_ph.negative_outlier_factor_
    df['temp_scores'] = clf_temp.negative_outlier_factor_
    df['tds_scores'] = clf_tds.negative_outlier_factor_
    df['turbidity_scores'] = clf_turbidity.negative_outlier_factor_



# Normalize negative outlier factor scores for color mapping
# Invert scores to positive, as more negative implies more of an outlier
    df['norm_ph_scores'] = (df['ph_scores'] - df['ph_scores'].min()) / (df['ph_scores'].max() - df['ph_scores'].min())
    df['norm_temp_scores'] = (df['temp_scores'] - df['temp_scores'].min()) / (df['temp_scores'].max() - df['temp_scores'].min())
    df['norm_tds_scores'] = (df['tds_scores'] - df['tds_scores'].min()) / (df['tds_scores'].max() - df['tds_scores'].min())
    df['norm_turbidity_scores'] = (df['turbidity_scores'] - df['turbidity_scores'].min()) / (df['turbidity_scores'].max() - df['turbidity_scores'].min())
    
    anomaly_threshold = 0.9
    df['ph_anomaly_flag'] = df['norm_ph_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    df['temp_anomaly_flag'] = df['norm_temp_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    df['tds_anomaly_flag'] = df['norm_tds_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    df['turbidity_anomaly_flag'] = df['norm_turbidity_scores'].apply(lambda x: 1 if x > anomaly_threshold else 0)
    return df







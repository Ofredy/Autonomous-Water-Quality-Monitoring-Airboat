import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from fake_data import *
import matplotlib.pyplot as plt 
from matplotlib.legend_handler import HandlerPathCollection
import pandas as pd  # Make sure to import pandas

X = np.reshape(ph, (-1, 1)) 
Y = np.reshape(temp,(-1,1))
Z = np.reshape(tds,(-1,1))
A = np.reshape(turbidity,(-1,1))
# Create a new LocalOutlierFactor instance for each parameter
clf_ph = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
clf_temp = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
clf_tds = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
clf_turbidity = LocalOutlierFactor(n_neighbors=20, contamination=0.1)

ph_pred = clf_ph.fit_predict(X)
temp_pred = clf_temp.fit_predict(Y)
tds_pred = clf_tds.fit_predict(Z)
turbidity_pred = clf_turbidity.fit_predict(A)


ph_errors = (ph_pred != ground_truth_ph).sum()
temp_errors = (temp_pred != ground_truth_temp).sum()
tds_errors = (tds_pred != ground_truth_tds).sum()
turbidity_errors = (turbidity_pred != ground_truth_turbidity).sum()

# Calculate the negative outlier factor scores for each parameter
ph_scores = clf_ph.negative_outlier_factor_
temp_scores = clf_temp.negative_outlier_factor_
tds_scores = clf_tds.negative_outlier_factor_
turbidity_scores = clf_turbidity.negative_outlier_factor_



# Normalize negative outlier factor scores for color mapping
# Invert scores to positive, as more negative implies more of an outlier
norm_ph_scores = (ph_scores - ph_scores.min()) / (ph_scores.max() - ph_scores.min())
norm_temp_scores = (temp_scores - temp_scores.min()) / (temp_scores.max() - temp_scores.min())
norm_tds_scores = (tds_scores - tds_scores.min()) / (tds_scores.max() - tds_scores.min())
norm_turbidity_scores = (turbidity_scores - turbidity_scores.min()) / (turbidity_scores.max() - turbidity_scores.min())






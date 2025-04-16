import pandas as pd
import numpy as np
from scipy import signal as sig
from scipy.stats import kurtosis, skew
import joblib

# Funzioni di feature extraction

def number_of_peaks_finding(array):
    prominence = 0.1 * (np.max(array) - np.min(array))
    peaks = sig.find_peaks(array, prominence=prominence)[0]
    return len(peaks)

def duration(df):
    t1 = pd.Timestamp(df["timestamp"].iloc[0])
    t2 = pd.Timestamp(df["timestamp"].iloc[-1])
    return (t2 - t1).total_seconds()

def smooth_n_peaks(array, n):
    kernel = np.ones(n) / n
    array_convolved = np.convolve(array, kernel, mode="same")
    return number_of_peaks_finding(array_convolved)

def smooth10_n_peaks(array): return smooth_n_peaks(array, 10)
def smooth20_n_peaks(array): return smooth_n_peaks(array, 20)
def diff_peaks(array): return number_of_peaks_finding(np.diff(array))
def diff2_peaks(array): return number_of_peaks_finding(np.diff(array, n=2))
def diff_var(array): return np.var(np.diff(array))
def diff2_var(array): return np.var(np.diff(array, n=2))

def gaps_squared(df):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["timestamp2"] = df["timestamp"].shift(1)
    df = df.iloc[1:]
    df["time_delta"] = (df["timestamp"] - df["timestamp2"]).dt.total_seconds()
    return np.sum(df["time_delta"] ** 2)

# Mappa delle feature
transformations = {
    "len": lambda x: len(x),
    "mean": np.mean,
    "var": np.var,
    "std": np.std,
    "kurtosis": kurtosis,
    "skew": skew,
    "n_peaks": number_of_peaks_finding,
    "smooth10_n_peaks": smooth10_n_peaks,
    "smooth20_n_peaks": smooth20_n_peaks,
    "diff_peaks": diff_peaks,
    "diff2_peaks": diff2_peaks,
    "diff_var": diff_var,
    "diff2_var": diff2_var,
}

# 🔍 Funzione finale di predizione
def predict_segment_anomaly(array_dict):
    # 1. Crea il DataFrame a partire dall'array di dizionari
    df = pd.DataFrame(array_dict)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    values = df["value"].values

    # 2. Calcola le feature
    features_calc = {}
    features_calc["duration"] = duration(df)
    for name, func in transformations.items():
        features_calc[name] = func(values)
    features_calc["gaps_squared"] = gaps_squared(df)
    features_calc["len_weighted"] = features_calc["len"]  # Assumi sampling=1
    features_calc["var_div_duration"] = features_calc["var"] / features_calc["duration"] if features_calc[
                                                                                                "duration"] != 0 else 0
    features_calc["var_div_len"] = features_calc["var"] / features_calc["len"] if features_calc["len"] != 0 else 0

    # 3. Prepara il DataFrame per la previsione
    X = pd.DataFrame([features_calc])

    # Riordina le colonne secondo l'ordine delle feature usate in training:
    COL_ORDER = [
        "mean", "var", "std", "len", "duration", "len_weighted", "gaps_squared", "n_peaks",
        "smooth10_n_peaks", "smooth20_n_peaks", "var_div_duration", "var_div_len",
        "diff_peaks", "diff2_peaks", "diff_var", "diff2_var", "kurtosis", "skew",
    ]
    X = X[COL_ORDER]

    return X


"""
    # 4. Carica scaler e modello
    scaler = joblib.load("scaler.pkl")
    model = joblib.load("modello_adaboost.pkl")

    # 5. Standardizza e predici
    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)

    return int(y_pred[0])  # 1 = anomaly, 0 = nominal
"""

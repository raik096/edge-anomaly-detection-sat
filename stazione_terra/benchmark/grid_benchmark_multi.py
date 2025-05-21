import os
import pandas as pd
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from pyod.models.inne import INNE
from pyod.models.knn import KNN
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
import more_itertools as mit
import numpy as np

# Percorsi
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(ROOT_DIR, "tmp/multimodel_aligned")
os.makedirs(TMP_DIR, exist_ok=True)

SEGMENT_PATH = os.path.join(ROOT_DIR, "satellite/stream_simulator/data/opssat/segments.csv")
RESULTS_PATH = os.path.join(TMP_DIR, "aligned_multimodel_results.csv")

CHANNELS = [f"CH{i}" for i in range(1, 10)]
MODELS = {
    "INNE": INNE,
    "KNN": KNN,
    "IForest": IForest,
    "LOF": LOF
}
CONTAMINATIONS = [0.01, 0.03]

CONTEXT_LENGTH = 144
STRIDE = 48
SMOOTHING_MIN_LENGTH = 4

if os.path.exists(RESULTS_PATH):
    os.remove(RESULTS_PATH)

def binary_series_to_intervals(binary_array):
    e_seqs = []
    if len(binary_array) > 0:
        groups = [list(group) for group in mit.consecutive_groups(binary_array)]
        e_seqs = [(int(g[0]), int(g[-1])) for g in groups]
    return e_seqs

def apply_smoothing(pred_labels):
    pred_labels = np.array(pred_labels)
    intervals = binary_series_to_intervals(np.where(pred_labels == 1)[0])
    smoothed_labels = np.zeros_like(pred_labels)
    for start, end in intervals:
        if (end - start + 1) >= SMOOTHING_MIN_LENGTH:
            smoothed_labels[start:end + 1] = 1
    return smoothed_labels.tolist()

def detect_large_diffs(norm_values, threshold=0.3):
    diffs = np.abs(np.diff(norm_values))
    flags = np.concatenate([[0], (diffs > threshold).astype(int)])
    return flags.tolist()

def expand_anomalies(pred_labels, expand=2):
    expanded = set()
    for i, v in enumerate(pred_labels):
        if v == 1:
            for j in range(max(0, i - expand), min(len(pred_labels), i + expand + 1)):
                expanded.add(j)
    return [1 if i in expanded else 0 for i in range(len(pred_labels))]

def compute_segment_metrics(df):
    pred_intervals = binary_series_to_intervals(df[df.pred_anomaly == 1].index.to_numpy())
    gt_intervals = binary_series_to_intervals(df[df.gt_anomaly == 1].index.to_numpy())

    matched_gt = set()
    tp, fp = 0, 0

    for pred in pred_intervals:
        pred_range = set(range(pred[0], pred[1] + 1))
        overlapping_gt_indices = [
            i for i, gt in enumerate(gt_intervals)
            if len(pred_range & set(range(gt[0], gt[1] + 1))) > 0
        ]
        if overlapping_gt_indices:
            for i in overlapping_gt_indices:
                if i not in matched_gt:
                    matched_gt.add(i)
                    tp += 1
                    break
            else:
                fp += 1
        else:
            fp += 1

    fn = len(gt_intervals) - len(matched_gt)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def run_aligned_benchmark():
    df = pd.read_csv(SEGMENT_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["gt_anomaly"] = df["anomaly"]

    channel_map = {
        "CADC0872": "CH1", "CADC0873": "CH2", "CADC0874": "CH3",
        "CADC0884": "CH4", "CADC0886": "CH5", "CADC0888": "CH6",
        "CADC0890": "CH7", "CADC0892": "CH8", "CADC0894": "CH9"
    }
    df["channel"] = df["channel"].map(channel_map)
    df = df[df["channel"].isin(CHANNELS)]

    for ch in tqdm(CHANNELS, desc="Modelli aligned con Chronos"):
        ch_df = df[df["channel"] == ch].copy()
        values = ch_df["value"].values.reshape(-1, 1)
        gt = ch_df["gt_anomaly"].values

        scaler = StandardScaler()
        norm_values = scaler.fit_transform(values).flatten()

        diff_flags = detect_large_diffs(norm_values, threshold=0.3)

        for model_name, model_class in MODELS.items():
            for cont in CONTAMINATIONS:
                pred_labels = [0] * len(norm_values)

                try:
                    for start in range(0, len(norm_values) - CONTEXT_LENGTH + 1, STRIDE):
                        window = norm_values[start:start + CONTEXT_LENGTH].reshape(-1, 1)
                        clf = model_class(contamination=cont)
                        clf.fit(window)
                        scores = clf.labels_
                        for i, label in enumerate(scores):
                            if label == 1:
                                pred_labels[start + i] = 1
                except Exception as e:
                    print(f"Errore su {ch}, {model_name}, cont={cont}: {e}")

                combined_labels = np.maximum(pred_labels, diff_flags)
                smoothed_labels = apply_smoothing(combined_labels)
                final_labels = expand_anomalies(smoothed_labels, expand=2)

                ch_df["pred_anomaly"] = final_labels
                metrics = compute_segment_metrics(ch_df)

                result_row = {
                    "channel": ch,
                    "model": model_name,
                    "contamination": cont,
                    **metrics
                }
                pd.DataFrame([result_row]).to_csv(
                    RESULTS_PATH, mode='a', index=False,
                    header=not os.path.exists(RESULTS_PATH)
                )

if __name__ == "__main__":
    run_aligned_benchmark()

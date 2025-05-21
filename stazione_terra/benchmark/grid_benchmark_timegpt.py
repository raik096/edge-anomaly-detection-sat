import os
import pandas as pd
import logging
import more_itertools as mit
from multiprocessing import Pool
from nixtla import NixtlaClient
import numpy as np

# Parametri generali
MIN_REQUIRED_SAMPLES = 350
WINDOW_SIZE = 144
STEP_SIZE = 48
REQUIRED_SAMPLES = 144
FREQ = '5s'
CONTEXT_LENGTH = 48
SMOOTHING_MIN_LENGTH = 3

TMP_DIR = "../../satellite/benchmark/tmp"
RESULTS_CSV = "./timegpt_benchmark_results.csv"
os.makedirs(TMP_DIR, exist_ok=True)

class TimeGPTStreamingDetector:
    def __init__(self, channel, freq='5s', level=90):
        self.channel = channel
        self.freq = freq
        self.level = level
        self.client = NixtlaClient(api_key="nixak-i6Pz6g6yO2j752CmZaLcS88gXp4HhKyzQvULXvcNBOcsPfjBdKU51bzW133mALBKLIBuM663W5bSj7ou")
        self.data = []
        self.predictions_list = []

    def update_context(self, value, timestamp, gt_anomaly):
        self.data.append({
            'unique_id': self.channel,
            'ds': pd.Timestamp("2024-01-01") + pd.Timedelta(seconds=5 * len(self.data)),
            'y': value,
            'timestamp': timestamp,
            'value': value,
            'gt_anomaly': gt_anomaly
        })

    def detect_all_windows(self):
        if len(self.data) < REQUIRED_SAMPLES:
            return

        df = pd.DataFrame(self.data).drop_duplicates(subset=['ds']).sort_values("ds")
        df = df.set_index("ds").asfreq(self.freq)
        rolling_window = min(96, max(12, len(df) // 10))
        df["y"] = (df["y"] - df["y"].rolling(rolling_window, min_periods=1).mean()) / df["y"].rolling(rolling_window, min_periods=1).std()
        df["y"] = df["y"].clip(-5, 5)
        df["unique_id"] = self.channel
        df = df.reset_index()

        results = []
        for start in range(0, len(df) - WINDOW_SIZE + 1, STEP_SIZE):
            window_df = df.iloc[start:start + WINDOW_SIZE].copy()
            if window_df["y"].isnull().any():
                continue
            try:
                result_df = self.client.detect_anomalies(window_df[["unique_id", "ds", "y"]], freq=self.freq, level=self.level)
                result_df = result_df.merge(window_df[["ds", "timestamp", "value", "gt_anomaly"]], on="ds", how="left")
                results.append(result_df)
            except Exception as e:
                logging.warning(f"[{self.channel}] Errore su finestra {start}-{start+WINDOW_SIZE}: {e}")

        if not results:
            return

        final_df = pd.concat(results).drop_duplicates(subset=["ds"]).sort_values("ds")

        final_df["pred_anomaly"] = final_df["anomaly"].astype(int)
        groups = [list(g) for g in mit.consecutive_groups(final_df.index[final_df["pred_anomaly"] == 1])]
        filtered_idx = [g for g in groups if len(g) >= SMOOTHING_MIN_LENGTH]
        flattened = [i for group in filtered_idx for i in group]
        final_df["pred_anomaly"] = 0
        final_df.loc[flattened, "pred_anomaly"] = 1

        for _, row in final_df.iterrows():
            self.predictions_list.append({
                "timestamp": row["timestamp"],
                "channel": self.channel,
                "value": row["value"],
                "pred_anomaly": int(row["pred_anomaly"]),
                "gt_anomaly": int(row.get("gt_anomaly", 0)),
                "normalized": False,
                "source_file": "segments.csv"
            })

def binary_series_to_intervals(binary_array):
    e_seqs = []
    if len(binary_array) > 0:
        groups = [list(group) for group in mit.consecutive_groups(binary_array)]
        e_seqs = [(int(g[0]), int(g[-1])) for g in groups if not g[0] == g[-1]]
    return e_seqs

def compute_segment_metrics(df):
    pred_intervals = binary_series_to_intervals(df["pred_anomaly"].values)
    gt_intervals = binary_series_to_intervals(df["gt_anomaly"].values)

    matched_gt = set()
    tp, fp = 0, 0

    for pred in pred_intervals:
        pred_range = set(range(pred[0], pred[1] + 1))
        overlaps = [
            i for i, gt in enumerate(gt_intervals)
            if len(pred_range & set(range(gt[0], gt[1] + 1))) > 0
        ]
        if overlaps:
            for i in overlaps:
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

def process_channel(args):
    ch, ch_df = args
    if len(ch_df) < MIN_REQUIRED_SAMPLES or ch_df["gt_anomaly"].sum() < 3:
        return None

    detector = TimeGPTStreamingDetector(channel=ch)
    for _, row in ch_df.iterrows():
        detector.update_context(row["value"], row["timestamp"], row["gt_anomaly"])
    detector.detect_all_windows()

    pred_df = pd.DataFrame(detector.predictions_list)
    if pred_df.empty:
        return None

    metrics = compute_segment_metrics(pred_df)
    return {
        "channel": ch,
        "context_length": CONTEXT_LENGTH,
        "model_variant": "timegpt_stream",
        **metrics
    }

def benchmark_timegpt_streaming(csv_path):
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["gt_anomaly"] = df["anomaly"]

    channel_map = {
        "CADC0872": "CH1", "CADC0873": "CH2", "CADC0874": "CH3",
        "CADC0884": "CH4", "CADC0886": "CH5", "CADC0888": "CH6",
        "CADC0890": "CH7", "CADC0892": "CH8", "CADC0894": "CH9"
    }
    df["channel"] = df["channel"].map(channel_map)
    df = df[df["channel"].isin(channel_map.values())]

    channel_dfs = [(ch, df[df["channel"] == ch].copy()) for ch in channel_map.values()]

    with Pool(processes=2) as pool:
        results = list(filter(None, pool.map(process_channel, channel_dfs)))

    if not results:
        print("❌ Nessun risultato.")
        return pd.DataFrame()

    df_results = pd.DataFrame(results)
    df_results.to_csv(RESULTS_CSV, index=False)

    tp = df_results["true_positives"].sum()
    fp = df_results["false_positives"].sum()
    fn = df_results["false_negatives"].sum()

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    global_metrics = pd.DataFrame([{
        "channel": "ALL",
        "context_length": CONTEXT_LENGTH,
        "model_variant": "timegpt_stream",
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }])
    global_metrics.to_csv("timegpt_stream_global_metrics.csv", index=False)

    print("✅ Benchmark completato.")
    return df_results

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    benchmark_timegpt_streaming("/satellite/stream_simulator/data/opssat/segments.csv")

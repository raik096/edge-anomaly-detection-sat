import pandas as pd
from abc import ABC

class ChronosBenchmarkBase(ABC):
    """
    Esegue il benchmarking delle predizioni a partire da un file CSV contenente:
    - 'timestamp', 'channel', 'pred_anomaly', 'gt_anomaly'
    - opzionalmente 'source_file' (aggiunto alla metrica finale)
    """
    def __init__(self, predictions_csv, channel=None, timestamp_col="timestamp"):
        self.pred_df = pd.read_csv(predictions_csv)
        self.timestamp_col = timestamp_col
        if channel:
            self.pred_df = self.pred_df[self.pred_df['channel'] == channel]
        self.pred_df[self.timestamp_col] = pd.to_numeric(self.pred_df[self.timestamp_col], errors="coerce")
        self.pred_df = self.pred_df.dropna(subset=[self.timestamp_col])
        self.pred_df[self.timestamp_col] = self.pred_df[self.timestamp_col].astype("int64")

        self.source_file = (
            self.pred_df["source_file"].iloc[0]
            if "source_file" in self.pred_df.columns and not self.pred_df["source_file"].isna().all()
            else "unknown"
        )

    def run(self):
        df = self.pred_df.dropna(subset=["gt_anomaly", "pred_anomaly"])
        if df.empty:
            print("⚠️ Nessun dato valido per il benchmark.")
            return self._empty_metrics()
        df["gt_anomaly"] = df["gt_anomaly"].astype(int)
        df["pred_anomaly"] = df["pred_anomaly"].astype(int)
        base_metrics = self.compute_segment_metrics(df)
        return {
            **base_metrics,
            "source_file": self.source_file
        }

    def compute_segment_metrics(self, df):
        pred_intervals = self.binary_series_to_intervals(df["pred_anomaly"].values)
        gt_intervals = self.binary_series_to_intervals(df["gt_anomaly"].values)

        tp, fp, fn = 0, 0, 0
        matched_pred = set()

        for gt in gt_intervals:
            matched = False
            for i, pred in enumerate(pred_intervals):
                if not (gt[1] < pred[0] or pred[1] < gt[0]):  # overlap
                    if i not in matched_pred:
                        tp += 1
                        matched_pred.add(i)
                        matched = True
                        break
            if not matched:
                fn += 1

        fp = len(pred_intervals) - len(matched_pred)

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

    def binary_series_to_intervals(self, series):
        intervals = []
        start = None
        for i, val in enumerate(series):
            if val == 1 and start is None:
                start = i
            elif val == 0 and start is not None:
                intervals.append((start, i - 1))
                start = None
        if start is not None:
            intervals.append((start, len(series) - 1))
        return intervals

    def _empty_metrics(self):
        return {
            "precision": 0.0, "recall": 0.0, "f1": 0.0,
            "true_positives": 0, "false_positives": 0,
            "false_negatives": 0
        }

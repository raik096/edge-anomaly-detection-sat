# benchmark/chronos_benchmark.py
import os
import pandas as pd
import numpy as np
from typing import Dict, Any

class ChronosBenchmark:
    def __init__(
        self,
        ground_truth_csv: str,
        predictions_csv: str,
        channel: str,
        value_col: str = "value",
        anomaly_gt_col: str = "anomaly",
        anomaly_pred_col: str = "anomaly",
        round_decimals: int = 8,
    ):
        """
        Args:
          - ground_truth_csv: CSV con colonne ['channel', 'timestamp', <value_col>, <anomaly_gt_col>, ...]
          - predictions_csv: CSV con ['channel', 'timestamp', <value_col>, <anomaly_pred_col>, ...]
          - channel: canale su cui filtrare
          - value_col: nome della colonna con il valore numerico
          - anomaly_gt_col: nome della colonna ground-truth
          - anomaly_pred_col: nome della colonna nelle predizioni
          - round_decimals: decimali per fare il merge su valore arrotondato
        """
        for path in (ground_truth_csv, predictions_csv):
            if not os.path.exists(path):
                raise FileNotFoundError(path)
        self.channel = channel
        self.gt_path = ground_truth_csv
        self.pred_path = predictions_csv
        self.val = value_col
        self.gt_an = anomaly_gt_col
        self.pred_an = anomaly_pred_col
        self.round_dec = round_decimals

        # carica subito GT
        self.df_gt = pd.read_csv(self.gt_path)
        if "channel" not in self.df_gt or self.val not in self.df_gt.columns:
            raise ValueError("GT CSV deve avere colonne 'channel' e '%s'" % self.val)
        if self.gt_an not in self.df_gt.columns:
            raise ValueError("GT CSV deve avere colonna '%s'" % self.gt_an)

        self.df_pred = None
        self.df_merged = None

    def load_data(self) -> None:
        # 1) leggi predizioni e filtra canale
        self.df_pred = pd.read_csv(self.pred_path)
        if "channel" not in self.df_pred.columns or self.val not in self.df_pred.columns:
            raise ValueError("Pred CSV deve avere colonne 'channel' e '%s'" % self.val)
        if self.pred_an not in self.df_pred.columns:
            raise ValueError("Pred CSV deve avere colonna '%s'" % self.pred_an)

        self.df_gt = self.df_gt[self.df_gt["channel"] == self.channel].copy()
        self.df_pred = self.df_pred[self.df_pred["channel"] == self.channel].copy()

        # 2) crea chiave arrotondata
        self.df_gt["_val_round"] = self.df_gt[self.val].round(self.round_dec)
        self.df_pred["_val_round"] = self.df_pred[self.val].round(self.round_dec)

        # 3) fai il merge su channel + chiave arrotondata
        self.df_merged = pd.merge(
            self.df_gt,
            self.df_pred,
            on=["channel", "_val_round"],
            how="inner",
            suffixes=("_gt", "_pred")
        )
        if self.df_merged.empty:
            raise RuntimeError("Nessun match sui valori arrotondati")

    def compute_metrics(self) -> Dict[str, Any]:
        if self.df_merged is None:
            raise ValueError("Carica prima i dati con load_data()")

        y_true = self.df_merged[f"{self.gt_an}_gt"].astype(int).values
        y_pred = self.df_merged[f"{self.pred_an}_pred"].astype(int).values

        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall    = tp / (tp + fn) if (tp + fn) else 0.0
        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        return {
            "n_matched": len(self.df_merged),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    def run(self) -> Dict[str, Any]:
        self.load_data()
        return self.compute_metrics()


if __name__ == "__main__":
    bench = ChronosBenchmark(
        ground_truth_csv="ground_truth.csv",
        predictions_csv="predictions.csv",
        channel="CADC0872",
        value_col="value",
        anomaly_gt_col="anomaly",
        anomaly_pred_col="anomaly",
        round_decimals=8
    )
    res = bench.run()
    print("Risultati:", res)

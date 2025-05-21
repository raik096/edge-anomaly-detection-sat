import ast
import os
import numpy as np
import pandas as pd
import time
from .base_datasource import DataSource


class NasaSource(DataSource):
    def __init__(self, dir_path=None):
        base_dir = os.path.dirname(__file__)

        if dir_path is None:
            # Usa il percorso corretto e assoluto
            self.dir_path = os.path.abspath(os.path.join(base_dir, "..", "data", "nasa", "test"))
        else:
            self.dir_path = dir_path

        self.anomaly_file = os.path.abspath(os.path.join(base_dir, "..", "data", "nasa", "labeled_anomalies.csv"))

    def stream(self):
        npy_files = [f for f in os.listdir(self.dir_path) if f.endswith(".npy")]
        print(os.path.join(self.dir_path))
        anomalies_df = pd.read_csv(self.anomaly_file)

        # Nel caso di NASA legge un channel.py e ne estrae i 9 canali
        for file_name in npy_files:

            anomalies = []                                                      # Anomalie trovate
            channel_id = file_name.split(".")[0]                                # Il canale viene trovato dal nome del file
            anomaly_df = anomalies_df[anomalies_df["chan_id"] == channel_id]    # Vettore
            anomaly_seq_df = anomaly_df["anomaly_sequences"]
            if len(anomaly_seq_df) > 0:
                anomalies = ast.literal_eval(anomaly_seq_df.values[0])

            data = np.load(os.path.join(self.dir_path, file_name))
            print(f"[DEBUG] Valori unici: {np.unique(data)}")
            df = pd.DataFrame(data)
            # tolgo le colonne con tutti 0
            nonzero_columns = np.where(data.any(axis=0))[0]

            for col in nonzero_columns[:9]:
                for i, row in df.iterrows():
                    # start: primo indice dove inizia la anomalia
                    # Crea una lista di booleani che controlla se i sta in start o in end per ogni canale,
                    # any fa l'OR tra tutti i booleani controllando se sono tutti false == false
                    gt_anomalies = any([start <= i <= end for start, end in anomalies])

                    yield {
                        "channel": f"CH{int(col)}",
                        "timestamp": int(time.time()),
                        "value": row[col],
                        # Campo aggiunto per il benchmark, ground_truth
                        "gt_anomaly": gt_anomalies

                    }
                    time.sleep(1)

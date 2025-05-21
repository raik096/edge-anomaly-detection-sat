import os
import pandas as pd
import time
from .base_datasource import DataSource

class OpssatSource(DataSource):
    MQTT_TOPICS_OPSSAT = {
        "CADC0872": "CH1", "CADC0873": "CH2", "CADC0874": "CH3",
        "CADC0884": "CH4", "CADC0886": "CH5", "CADC0888": "CH6",
        "CADC0890": "CH7", "CADC0892": "CH8", "CADC0894": "CH9"
    }

    def __init__(self, csv_path=None):
        base_dir = os.path.dirname(__file__)

        if csv_path is None:
            # Percorso assoluto rispetto alla struttura del progetto
            self.csv_path = os.path.abspath(os.path.join(base_dir, "..", "data", "opssat", "segments.csv"))
        else:
            self.csv_path = csv_path

    def stream(self):
        df = pd.read_csv(self.csv_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"]).astype(int) // 10 ** 9

        # ✅ Ordina i dati in base al timestamp
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        for _, row in df.iterrows():
            yield {
                "channel": self.MQTT_TOPICS_OPSSAT[row["channel"]],
                #"timestamp": int(row["timestamp"]),  # Usa questo se fai benchmark
                "timestamp": int(time.time()),
                "value": row["value"],
                "gt_anomaly": row["anomaly"]
            }
            time.sleep(1)

    """
    def stream(self):
        df = pd.read_csv(self.csv_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"]).astype(int) // 10**9
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        previous_time = None

        for _, row in df.iterrows():
            current_time = row["timestamp"]
            #if previous_time is not None:
            #    delta_t = current_time - previous_time
            #    if delta_t > 0:
            #        time.sleep(delta_t)
            #time.sleep(1)
            #print(row)

            yield {
                "channel": self.MQTT_TOPICS_OPSSAT[row["channel"]],
                #"timestamp": row["timestamp"],  # <--- per il benchmarking
                "timestamp": int(time.time()),  #<--- per non benchmarking
                "value": row["value"],
                # Campo aggiunto per il benchmark, ground_truth
                "gt_anomaly": row["anomaly"]
            }
            #previous_time = current_time
    """

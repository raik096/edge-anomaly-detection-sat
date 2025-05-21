# satellite/canale/channel.py
import os
import pandas as pd
from datetime import datetime
from satellite.models.modelStrategy import ModelStrategy

LOG_PATH = "benchmark/light_log.csv"
os.makedirs("benchmark", exist_ok=True)

class Channel:
    """
    Classe responsabile della gestione del canale singolo, compresa strategia, stato e log.
    """
    def __init__(self, name: str, strategy: ModelStrategy):
        self.name = name
        self.strategy = strategy
        self.active = True
        self.anomaly_count = 0

    def set_strategy(self, strategy: ModelStrategy):
        self.strategy = strategy

    def process(self, payload) -> int:
        """Esegue un passo di inferenza sul payload e aggiorna lo stato interno."""
        if not self.active:
            return 0
        if not isinstance(self.strategy, ModelStrategy):
            raise TypeError("Strategy non valida: deve implementare ModelStrategy")

        value = payload["value"]
        timestamp = payload.get("timestamp")
        self.strategy.forecast()
        anomaly = self.strategy.detect_anomaly(value)
        self.strategy.update_context(value, timestamp, self.name)
        self.strategy.accumulate_and_save(payload, anomaly)
        self.anomaly_count += anomaly
        return anomaly

    def log_summary(self):
        detector = self.strategy
        mean_width = (detector.max_q - detector.min_q) if detector.min_q and detector.max_q else None
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": self.name,
            "context_length": detector.context_length,
            "quantile": detector.quantile_levels[2],
            "smoothing": detector.smoothing,
            "margin": detector.margin,
            "anomaly_count": self.anomaly_count,
            "mean_range_width": mean_width,
            "min_predicted": detector.min_q,
            "max_predicted": detector.max_q
        }
        df = pd.DataFrame([data])
        df.to_csv(LOG_PATH, mode="a", header=not os.path.exists(LOG_PATH), index=False)
        self.anomaly_count = 0

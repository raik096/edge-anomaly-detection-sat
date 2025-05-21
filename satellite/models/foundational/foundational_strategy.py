from abc import ABC, abstractmethod

from satellite.models.modelStrategy import ModelStrategy


class FoundationalModelStrategy(ModelStrategy, ABC):

    @abstractmethod
    def forecast(self):
        """Logica di previsione del prossimo dato"""

    def accumulate_and_save(self, payload, anomaly):

        self.predictions_list.append({
            "timestamp": payload["timestamp"],
            "channel": payload["channel"],
            "value": payload["value"],
            "min_quantile": self.min_q,
            "max_quantile": self.max_q,
            "pred_anomaly": anomaly,
            "gt_anomaly": payload.get("gt_anomaly", 0),
            "normalized": self.normalize,
            "source_file": payload.get("source_file", "unknown")
        })

    @abstractmethod
    def detect_anomaly(self, value):
        pass


from abc import ABC, abstractmethod
import torch
import numpy as np
from sklearn.preprocessing import StandardScaler
from satellite.models.modelStrategy import ModelStrategy

class UnsupervisedModelStrategy(ModelStrategy, ABC):
    def __init__(self, model, context_length=144):
        self.model = model
        self.context_length = context_length
        self.scaler = StandardScaler()
        self.window = []
        self.fitted = False
        self.predictions_list = []
        self.context_tensor = torch.zeros(context_length, dtype=torch.float32)

    def fit(self):
        if len(self.window) < self.context_length:
            return
        window = np.array(self.window[-self.context_length:]).reshape(-1, 1)
        window = self.scaler.fit_transform(window)
        self.model.fit(window)
        self.fitted = True

    def forecast(self):
        if not self.fitted:
            return None, 0.0
        return self.predict(self.context_tensor)

    def predict(self, context_tensor):
        x = self.scaler.transform(context_tensor.reshape(-1, 1))
        return None, self.model.predict(x)

    def update_context(self, value, timestamp=None, channel=None):
        if len(self.window) > self.context_length:
            self.window.pop(0)
        self.window.append(value)
        self.context_tensor = torch.cat(
            [self.context_tensor[1:], torch.tensor([value], dtype=torch.float32)]
        )

    def detect_anomaly(self, value):
        self.update_context(value)
        self.fit()
        if not self.fitted:
            return 0
        _, scores = self.predict(np.array(self.window[-self.context_length:]))
        return int(np.any(scores))

    def accumulate_and_save(self, payload, anomaly):
        self.predictions_list.append({
            "timestamp": payload["timestamp"],
            "channel": payload["channel"],
            "value": payload["value"],
            "pred_anomaly": anomaly,
            "gt_anomaly": payload.get("gt_anomaly", 0),
            "normalized": False,
            "source_file": payload.get("source_file", "unknown")
        })

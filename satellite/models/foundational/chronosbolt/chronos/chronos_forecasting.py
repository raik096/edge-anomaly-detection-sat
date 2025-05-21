import torch
import pandas as pd
import numpy as np
from chronos import BaseChronosPipeline
from satellite.detectors.diff import DiffDetector
from satellite.models.foundational.foundational_strategy import FoundationalModelStrategy
from satellite.detectors.strategy_detector import StrategyDetector

class ChronosAnomalyDetector(FoundationalModelStrategy):
    def __init__(self, model_variant="mini", batch_size=1,
                 context_length=24,
                 prediction_length=1,
                 quantile_levels=[0.1, 0.5, 0.9],
                 margin=0.01,
                 smoothing=False,
                 detection_strategy="diff",
                 normalize=True,
                 strategy_detector: StrategyDetector = DiffDetector()):

        self._name = "ChronosBolt" + model_variant
        self.prediction_length = prediction_length
        self.context_length = context_length
        self.quantile_levels = quantile_levels
        self.margin = margin
        self.smoothing = smoothing
        self.batch_size = batch_size
        self.predictions_list = []
        self.detection_strategy = detection_strategy
        self.normalize = normalize
        self.value_stats = {}
        self.recent_values = []
        self.detector = strategy_detector

        self.pipeline = BaseChronosPipeline.from_pretrained(
            f"amazon/chronos-bolt-{model_variant}",
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
        self.context_window = []
        self.context_tensor = torch.zeros(context_length, dtype=torch.float32)

        self.min_q = None
        self.max_q = None
        self.quantiles = None

    def update_context(self, value, timestamp=None, channel=None):
        if self.normalize:
            if channel not in self.value_stats:
                self.value_stats[channel] = {"values": [], "mean": 0, "std": 1}

            stats = self.value_stats[channel]
            stats["values"].append(value)
            if len(stats["values"]) > self.context_length * 3:
                stats["values"].pop(0)
            stats["mean"] = np.mean(stats["values"])
            stats["std"] = max(np.std(stats["values"]), 1e-8)
            value = (value - stats["mean"]) / stats["std"]

        if len(self.context_window) >= self.context_length:
            self.context_window.pop(0)
        self.context_window.append(value)
        self.context_tensor = torch.cat(
            [self.context_tensor[1:], torch.tensor([value], dtype=torch.float32)]
        )

    def forecast(self):
        if len(self.context_window) < self.context_length:
            self.quantiles = None
            return

        self.quantiles, _ = self.pipeline.predict_quantiles(
            context=self.context_tensor,
            prediction_length=self.prediction_length,
            quantile_levels=self.quantile_levels,
        )
        self.min_q = self.quantiles[0, 0, 0].item()
        self.max_q = self.quantiles[0, 0, 2].item()

    def detect_anomaly(self, value):
        self.recent_values.append(value)
        if len(self.recent_values) > 3:
            self.recent_values.pop(0)

        if self.quantiles is None or torch.isnan(self.quantiles).any():
            return 0

        if self.prediction_length == 1:
            lower = self.quantiles[0, 0, 0].item() - self.margin
            upper = self.quantiles[0, 0, 2].item() + self.margin
        else:
            min_vals = self.quantiles[0, :, 0]
            max_vals = self.quantiles[0, :, 2]
            lower = min_vals.min().item() - self.margin
            upper = max_vals.max().item() + self.margin

        if self.detector:
            return int(self.detector.detect_anomaly(self.recent_values, lower, upper))
        else:
            print("⚠️ Nessuna StrategyDetector fornita. Uso fallback 'naive'.")
            return int(value < lower or value > upper)

    @property
    def name(self) -> str:
        return self._name
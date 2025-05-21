from satellite.models.modelStrategy import ModelStrategy
from satellite.models.foundational.foundational_strategy import FoundationalModelStrategy
from satellite.detectors.strategy_detector import StrategyDetector
from nixtla import NixtlaClient
import pandas as pd
from datetime import datetime

class TimeGPT(FoundationalModelStrategy):
    def __init__(self, channel, detector: StrategyDetector = None, level=90, freq='5s'):
        self.channel = channel
        self.freq = freq
        self.level = level
        self.client = NixtlaClient(...)
        self.data = []
        self.predictions_list = []
        self.detector = detector
        self.min_q = None
        self.max_q = None
        self.margin = 0.05  # può essere parametrico
        self.recent_values = []

    def update_context(self, value, timestamp=None, channel=None):
        self.recent_values.append(value)
        if len(self.recent_values) > 3:
            self.recent_values.pop(0)
        self.data.append({
            'unique_id': self.channel,
            'ds': pd.Timestamp("2024-01-01") + pd.Timedelta(seconds=5 * len(self.data)),
            'y': value,
            'timestamp': timestamp,
            'value': value
        })

    def detect_anomaly(self, value):
        if self.min_q is None or self.max_q is None:
            return 0
        lower = self.min_q - self.margin
        upper = self.max_q + self.margin
        if self.detector:
            return int(self.detector.detect_anomaly(self.recent_values, lower, upper))
        else:
            return int(value < lower or value > upper)

    def name(self) -> str:
        return "TimeGPT"
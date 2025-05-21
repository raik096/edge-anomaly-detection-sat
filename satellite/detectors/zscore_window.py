from typing import List
from strategy_detector import StrategyDetector
import numpy as np

class ZScoreWindowDetector(StrategyDetector):
    """
    Rileva un'anomalia se la media dei valori recenti si discosta troppo
    dal centro del range [lower, upper], normalizzato per l'ampiezza.
    """

    def __init__(self, window_size=5, threshold=1.5):
        self.window_size = window_size
        self.threshold = threshold
        self.recent_values = []

    def detect_anomaly(self, value, lower, upper):
        self.recent_values.append(value)
        if len(self.recent_values) > self.window_size:
            self.recent_values.pop(0)

        center = (upper + lower) / 2
        range_width = max(upper - lower, 1e-6)  # evita divisione per zero
        score = abs(np.mean(self.recent_values) - center) / range_width
        return int(score > self.threshold)

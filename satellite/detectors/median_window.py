from strategy_detector import StrategyDetector
import numpy as np

class MedianWindowDetector(StrategyDetector):

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.recent_values = []

    def detect_anomaly(self, value, lower, upper):
        self.recent_values.append(value)
        if len(self.recent_values) > self.window_size:
            self.recent_values.pop(0)

        agg_value = np.median(self.recent_values)
        return int(agg_value < lower or agg_value > upper)

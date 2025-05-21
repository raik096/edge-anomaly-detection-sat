from satellite.detectors.strategy_detector import StrategyDetector

class DiffDetector(StrategyDetector):
    def __init__(self, threshold_ratio=0.3):
        self.threshold_ratio = threshold_ratio

    def detect_anomaly(self, values, lower, upper):
        if len(values) < 2:
            return False
        diff = abs(values[-1] - values[-2])
        threshold = (upper - lower) * self.threshold_ratio
        return diff > threshold

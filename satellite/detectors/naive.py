from satellite.detectors.strategy_detector import StrategyDetector


class NaiveDetector(StrategyDetector):
    """
    Rileva un'anomalia se il valore corrente è fuori dai quantili (naive thresholding).
    Tiene traccia degli ultimi N valori solo se necessario.
    """

    def __init__(self, window_size=3):
        self.window_size = window_size
        self.recent_values = []

    def detect_anomaly(self, value, lower, upper):
        self.recent_values.append(value)
        if len(self.recent_values) > self.window_size:
            self.recent_values.pop(0)

        # Anomalia se il valore è fuori dai limiti
        return int(value < lower or value > upper)

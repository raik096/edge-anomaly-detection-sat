from satellite.detectors.diff import DiffDetector
from satellite.detectors.mean_window import MeanWindowDetector
from satellite.detectors.median_window import MedianWindowDetector
from satellite.detectors.naive import NaiveDetector
from satellite.detectors.zscore_window import ZScoreWindowDetector

def get_detector(strategy: str):

    match strategy:
        case "diff":
            return DiffDetector()
        case "mean_window":
            return MeanWindowDetector()
        case "median_window":
            return MedianWindowDetector()
        case "naive":
            return NaiveDetector()
        case "zscore_window":
            return ZScoreWindowDetector()
        case _:
            raise ValueError(f"Strategia '{strategy}' non riconosciuta.")



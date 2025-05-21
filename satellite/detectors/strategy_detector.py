from abc import ABC, abstractmethod
from typing import List

class StrategyDetector(ABC):
    """
    Interfaccia per strategie di rilevamento anomalie.
    """
    @abstractmethod
    def detect_anomaly(self, values: List[float], lower: float, upper: float) -> bool:
        """
        Determina se l'ultimo valore in 'values' è anomalo rispetto ai limiti dati.
        """
        pass

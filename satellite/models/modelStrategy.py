from abc import ABC, abstractmethod

"""
Il modello perché sia implementato deve sovrascrivere i metodi:
    - load_self: dove si istanzia
    - fit: dove predice il prossimo valore in base alla sliding window
    - predict: restituisce se il valore riscontrato è un anomalia o meno
    - name: ritorna il proprio nome
"""

class ModelStrategy(ABC):
    """
    Interfaccia astratta per le diverse strategie di modelli tra cui:
        - Foundational Models (ChronosBolt, TimeGPT)
        - Unsupervised Models (INNE, IForest, KNN, LOF)
    """
    @abstractmethod
    def name(self) -> str:
        """Nome descrittivo della strategia."""
        pass

    @abstractmethod
    def forecast(self):
        pass

    @abstractmethod
    def detect_anomaly(self, value) -> bool:
        pass

    @abstractmethod
    def update_context(self, value, timestamp=None, channel=None):
        """Default: ignora timestamp e channel se non servono."""
        pass

    @abstractmethod
    def accumulate_and_save(payload, anomaly):
        pass
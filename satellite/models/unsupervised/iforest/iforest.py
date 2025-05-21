from pyod.models.iforest import IForest
from satellite.models.unsupervised.unsupervised_strategy import UnsupervisedModelStrategy

class IForestModel(UnsupervisedModelStrategy):
    def __init__(self):
        super().__init__(model=IForest())

    def name(self) -> str:
        return "IForest"

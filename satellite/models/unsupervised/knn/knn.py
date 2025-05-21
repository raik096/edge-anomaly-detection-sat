from pyod.models.knn import KNN
from satellite.models.unsupervised.unsupervised_strategy import UnsupervisedModelStrategy

class KNNMModel(UnsupervisedModelStrategy):
    def __init__(self):
        super().__init__(model=KNN())

    def name(self) -> str:
        return "KNN"
from pyod.models.inne import INNE
from satellite.models.unsupervised.unsupervised_strategy import UnsupervisedModelStrategy

class INNEModel(UnsupervisedModelStrategy):
    def __init__(self):
        super().__init__(model=INNE())

    def name(self) -> str:
        return "INNE"

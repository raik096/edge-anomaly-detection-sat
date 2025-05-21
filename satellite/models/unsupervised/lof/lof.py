from pyod.models.lof import LOF
from satellite.models.unsupervised.unsupervised_strategy import UnsupervisedModelStrategy

class LOFModel(UnsupervisedModelStrategy):
    def __init__(self):
        super().__init__(model=LOF())

    def name(self) -> str:
        return "LOF"

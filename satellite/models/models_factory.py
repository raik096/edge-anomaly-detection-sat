from satellite.models.foundational.chronosbolt.chronos.chronos_forecasting import ChronosAnomalyDetector
from satellite.models.foundational.timegpt.timegpt_forecasting import TimeGPT
from satellite.models.unsupervised.iforest.iforest import IForestModel
from satellite.models.unsupervised.inne.inne import INNEModel
from satellite.models.unsupervised.knn.knn import KNNMModel
from satellite.models.unsupervised.lof.lof import LOFModel


def get_model(model_name: str):
    if model_name == "chronosbolt":
        return ChronosAnomalyDetector()
    if model_name == "timegpt":
        return TimeGPT()
    if model_name == "inne":
        return INNEModel()
    if model_name == "lof":
        return LOFModel()
    if model_name == "knn":
        return KNNMModel()
    if model_name == "iforest":
        return IForestModel()
""" FILE RESPONSABILE NELLA GESTIONE DEI DATI SIMULATI OPS-SAT e NASA

Questo file si preoccupa di raccogliere, leggendo i dati dalle sorgenti CSV, i valori
corrispondenti ai canali, crea una dataframe sfruttando pandas e legge l'intero file,
accedendo al campo dataframe["timestamp"] modifico il tipo della data portandolo in formato
UNIX in secondi, ordino il dataframe in base al timestamp, e leggo riga per riga,
trasmettendo tramite protocollo vanilla-UDP (senza logica ulteriore), l'intero dataset.

I dati vengono serializzati in JSON
    {"channel": stringa,
        "timestamp": intero,
        "valore": intero}

# La descrizione dei canali viene omogeneizzata, dove CH1 in OPSSAT sta per CADC0872
# mentre in NASA sta per sensore 1.
# MQTT_TOPICS_OPSSAT = [    <-- MAPPATURA
#     "CADC0872" ==  CH1,
#     "CADC0873" ==  CH2,
#     "CADC0874" ==  CH3,
#     "CADC0884" ==  CH4,
#     "CADC0886" ==  CH5,
#     "CADC0888" ==  CH6,
#     "CADC0890" ==  CH7,
#     "ADC0892" ==   CH8,
#     "CADC0894" ==  CH9
# ]

BENCHMARK MODE: ON

Il simulatore inserisce nel file CSV ground_truth la colonna timestamp
in modo da poter, una volta fatto alcune predizioni, confrontare le anomalie
e i valori predetti.

"""
from abc import ABC, abstractmethod

class DataSource(ABC):
    @abstractmethod
    def stream(self):
        """
        Generatore che restituisce un dizionario con i campi:
        - channel (str)
        - timestamp (int)
        - value (int/float)
        """
        pass

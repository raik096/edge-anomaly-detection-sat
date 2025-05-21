# FILE CONFIGURAZIONE PER mainS.py

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
# MQTT_BROKER = "localhost"
MQTT_BROKER = "172.17.0.1" # All'interno del container
MQTT_PORT = 1883
MODEL_PATH = "amazon/chronos-bolt-small"
PREDICTION_LENGTH = 1
MAX_WINDOW_CHRONOS_LENGHT = 100

# faccio il summury dopo 300 predizioni
BENCHMARK_COUNTER = 300

# Permetto il monitoring del dispositivo edge ciò comporta:
#   - Un overhead dovuta a MQTT
STRATEGYMODEL = "chronosbolt"
PLOTTING = False
MONITORING = True
NORMALIZATION = False
DETTAGLIO = ["ALTO", "NORMALE"]
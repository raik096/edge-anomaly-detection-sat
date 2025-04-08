##################################################
#
# Questo file serve per simulare la stazione terra
#   - riceve i dati dai 9 canali MQTT mosquitto
#   - questi canali trasmettono un valore che vorrei riportare a influxDB
#   - il valore da riportare sarà inizialmente lo stesso
#   - in una seconda implementazione conviene che siano stati processati
#
# per processare i dati è necessario che chiami le funzioni dedicate scritte in
# influxdb_tools in modo che possa comodamente scrivere valori specificando il dato
##################################################

import json

import numpy as np
import paho.mqtt.client as mqtt
from db_gf import influxdb_tools as idb_tools
from collections import deque
from stazione_terra.ada_boost_classifier import AdaBoostClassifierPredict
from stazione_terra.features_extractor import predict_segment_anomaly

ID_SATELLITE = 1
# valori massimi su cui calcolare le anomalie
MAX_VALUES_FOR_AD = 4

# Configurazioni MQTT
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPICS = [
    "CADC0872", "CADC0873", "CADC0874", "CADC0884",
    "CADC0886", "CADC0888", "CADC0890", "ADC0892", "CADC0894"
]

current_block = {
    "timestamp": None,
    "data": {topic: None for topic in MQTT_TOPICS}
}

buffer = []

def flush_block():
    if current_block["timestamp"] is not None:
        idb_tools.writetodb(current_block["timestamp"], current_block["data"])

def on_connect(client, userdata, flags, rc):
    print(f"🔗 Connected with result code {rc}")

    client.subscribe("sensori/#")
    # Sottoscrizione ai topic
    #for topic in MQTT_TOPICS:
    #    client.subscribe(f"sensori/{topic}")
    #    print(f"✅ Sottoscritto a sensori/{topic}")


def on_subscribe(client, userdata, mid, granted_qos):
    print(f"✅ Message {mid} published with QoS {granted_qos}")


# Funzione per processare i messaggi MQTT
def on_message(client, userdata, msg):
    global current_block
    global buffer
    print(f"Messaggio ricevuto su {msg.topic}")

    try:
        payload = json.loads(msg.payload.decode())
        timestamp = payload.get("timestamp")
        value = payload.get("value")
        topic = msg.topic.split("/")[-1]  # Estrae il nome del canale dal topic (es: sensori/CADC0872 → CADC0872)
        buffer.append(payload)

        if len(buffer) >= MAX_VALUES_FOR_AD:
            hotpotato = predict_segment_anomaly(buffer)
            AdaBoostClassifierPredict(hotpotato)
            buffer = []

        if timestamp is None or value is None:
            print("❌ Messaggio incompleto ricevuto.")
            return

        if current_block["timestamp"] is None:
            # Siamo nel caso del primo messaggio ricevuto
            current_block["timestamp"] = timestamp
        elif timestamp > current_block["timestamp"]:
            # Messaggio nuovo → flush precedente blocco e inizia uno nuovo
            # print(current_block)
            flush_block()
            current_block["timestamp"] = timestamp
            # Reimposto tutto da capo
            current_block["data"] = {topic: None for topic in MQTT_TOPICS}

        current_block["data"][topic] = value

    except json.JSONDecodeError:
        print("❌ Errore nel parsing del messaggio JSON.")
    except Exception as e:
        print(f"❌ Errore durante l'elaborazione del messaggio: {e}")

if __name__ == "__main__":
    # Creo il client MQTT
    idb_tools.initInfluxDBClient()
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_subscribe = on_subscribe

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("MQTT Broker online")
    mqtt_client.loop_forever()
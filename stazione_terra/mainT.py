import json
import time
import paho.mqtt.client as mqtt
from satellite.config import NORMALIZATION
from stazione_terra.utilities import influxdb_tools as idb_tools
from stazione_terra.utilities.influxdb_tools import send_anomaly_to_influxDB, send_hwtelemetry_to_influxDB

ID_SATELLITE = 0  # 0 per OPSSAT, 1 per NASA
MAX_VALUES_FOR_AD = 20

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPICS = [f"CH{i}" for i in range(10)]

print("📡 MQTT Topics:", MQTT_TOPICS)

current_block = {
    "timestamp": None,
    "data": {topic: None for topic in MQTT_TOPICS}
}

buffer = []
channel_stats = {topic: {"min": float("inf"), "max": float("-inf")} for topic in MQTT_TOPICS}

# Flush del blocco di dati verso InfluxDB
def flush_block():
    if current_block["timestamp"] is not None:
        idb_tools.send_msg_to_influxDB("satellite1", current_block["timestamp"], current_block["data"])
        print(f"📤 Blocco inviato a InfluxDB: timestamp {current_block['timestamp']}")

# Connessione al broker MQTT
def on_connect(client, userdata, flags, rc):
    print(f"🔗 Connesso al broker MQTT con codice {rc}")
    client.subscribe("sensori/#")
    client.subscribe("hwtelemetry")

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"✅ Subscription {mid} con QoS {granted_qos}")

# Messaggi MQTT ricevuti
def on_message(client, userdata, msg):
    global current_block, buffer

    print(f"📨 Topic: {msg.topic} | Payload: {msg.payload.decode()}")

    if msg.topic.startswith("sensori/"):
        process_sensor_message(msg)
    elif msg.topic == "hwtelemetry":
        process_hwtelemetry_message(msg)

# Gestione messaggi sensori (anomaly detection + flush blocco)
def process_sensor_message(msg):
    global current_block, buffer

    try:
        payload = json.loads(msg.payload.decode())
        timestamp = payload.get("timestamp")
        value = payload.get("value")
        topic = msg.topic.split("/")[-1]
        is_anomaly = payload.get("anomaly")

        #if NORMALIZATION:
        #    value = normalize_value(value, topic)

        if timestamp is None or value is None:
            print("⚠️  Messaggio sensore incompleto.")
            return

        buffer.append(payload)
        # In questo caso il messaggio dovrebbe già avere l'informazione che è un anomalia

        # Applica AD su un segmento
        #if len(transmitter) >= MAX_VALUES_FOR_AD:
        #    segment = predict_segment_anomaly(transmitter)
        #    isAnomaly, Y_score = AdaBoostClassifierPredict(segment)

#------- INVIO DATO
        if is_anomaly:
            send_anomaly_to_influxDB(timestamp, topic, value, "Anomalia rilevata da AD")
            print(f"🚨 Anomalia: {topic} @ {timestamp} (score={value})")
        else:
            print(f"✅ Normale. Score: {value}")

        buffer = []

        # Gestione blocchi di invio
        if current_block["timestamp"] is None:
            current_block["timestamp"] = timestamp
        elif timestamp > current_block["timestamp"]:
            flush_block()
            current_block["timestamp"] = timestamp
            current_block["data"] = {topic: None for topic in MQTT_TOPICS}

        current_block["data"][topic] = value

    except json.JSONDecodeError:
        print("❌ Errore nel parsing JSON sensore.")
    except Exception as e:
        print(f"❌ Errore elaborazione messaggio sensore: {e}")

# Gestione hwtelemetry
def process_hwtelemetry_message(msg):
    try:
        payload = json.loads(msg.payload.decode())
        timestamp = int(time.time() * 1e9)  # ns per InfluxDB

        send_hwtelemetry_to_influxDB(
            cpu_percent=payload.get("cpu_percent"),
            temperature=payload.get("temperature"),
            memory_percent=payload.get("memory_percent"),
            disk_percent=payload.get("disk_percent"),
            network_throughput_sent_KBps=payload.get("network_throughput_sent_KBps"),
            network_throughput_recv_KBps=payload.get("network_throughput_recv_KBps"),
            mean_prediction_time_ms=payload.get("mean_prediction_time_ms"),
            timestamp=timestamp,
            channel="telemetry",
            description="status"
        )

        print("📡 Telemetria hardware inviata")

    except Exception as e:
        print(f"❌ Errore durante il parsing/invio hwtelemetry: {e}")

def normalize_value(value, topic):
    stats = channel_stats[topic]
    stats["min"] = min(stats["min"], value)
    stats["max"] = max(stats["max"], value)

    if stats["max"] == stats["min"]:  # evita divisione per zero
        return 0.5  # valore neutro

    return (value - stats["min"]) / (stats["max"] - stats["min"])

# MAIN
if __name__ == "__main__":
    idb_tools.init_InfluxDB_Client()

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_subscribe = on_subscribe

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("🚀 Stazione Terra pronta e in ascolto...")

    mqtt_client.loop_forever()

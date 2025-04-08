import socket
import json
import paho.mqtt.client as mqtt

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

MQTT_BROKER = "172.17.0.1"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🔗 Connected to MQTT Broker!", flush=True)
    else:
        print(f"❌ Failed to connect to MQTT Broker with code {rc}", flush=True)


def on_publish(client, userdata, mid):
    print(f"✅ Message {mid} published", flush=True)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on {UDP_IP}:{UDP_PORT}...", flush=True)

while True:
    try:
        data, addr = sock.recvfrom(1024)
        payload = json.loads(data.decode())

        channel = payload.get("channel")
        timestamp = payload.get("timestamp")
        value = payload.get("value")

        if channel and timestamp and value is not None:
            mqtt_topic = f"sensori/{channel}"
            mqtt_message = json.dumps({"timestamp": timestamp, "value": value})

            mqtt_client.publish(mqtt_topic, mqtt_message, retain=True)
            print(f"📡 Published to {mqtt_topic}: {mqtt_message}")

    except json.JSONDecodeError:
        print("❌ Errore nel parsing JSON")
    except Exception as e:
        print(f"❌ Errore: {e}")
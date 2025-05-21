import paho.mqtt.client as mqtt
from satellite.transmitter.buffered_transmitter import BufferedTransmitter

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🔗 Connected to MQTT Broker!", flush=True)
    else:
        print(f"❌ Failed to connect to MQTT Broker with code {rc}", flush=True)

def setup_mqtt_client(broker: str, port: int) -> mqtt.Client:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(broker, port, 60)
    client.loop_start()
    return client

def setup_transmitter(broker: str, port: int, topic_prefix: str = "sensori") -> BufferedTransmitter:
    client = setup_mqtt_client(broker, port)
    return BufferedTransmitter(client, topic_prefix)

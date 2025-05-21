import time
from collections import deque

class BufferedTransmitter:
    def __init__(self, mqtt_client, topic_prefix="", max_age_seconds=600, max_buffer_size=1000):
        """
        :param mqtt_client: istanza configurata di paho.mqtt.client.Client
        :param topic_prefix: prefisso del topic MQTT (es. "sensori")
        :param max_age_seconds: tempo massimo di vita di un messaggio nel buffer (default: 10 minuti)
        :param max_buffer_size: numero massimo di messaggi nel buffer
        """
        self.client = mqtt_client
        self.topic_prefix = topic_prefix.rstrip("/")
        self.max_age = max_age_seconds
        self.max_buffer_size = max_buffer_size
        self.buffer = deque()

    def _build_topic(self, topic_suffix):
        if self.topic_prefix:
            return f"{self.topic_prefix}/{topic_suffix}"
        return topic_suffix

    def send(self, topic_suffix, payload: str, retain=True):
        """Prova a inviare il messaggio. In caso di errore, lo bufferizza."""
        topic = self._build_topic(topic_suffix)
        timestamp = time.time()

        try:
            result = self.client.publish(topic, payload, retain=retain)
            if result.rc != 0:
                raise Exception(f"publish returned error code {result.rc}")
        except Exception as e:
            print(f"⚠️ MQTT publish failed: {e} — buffering message.")
            if len(self.buffer) < self.max_buffer_size:
                self.buffer.append((timestamp, topic, payload, retain))
            else:
                print(f"🗑️ Buffer pieno: scartato messaggio per {topic}")
        self.retry_buffered()

    def retry_buffered(self):
        """Tenta di ripubblicare i messaggi bufferizzati più recenti."""
        now = time.time()
        new_buffer = deque()

        while self.buffer:
            t, topic, payload, retain = self.buffer.popleft()
            if now - t > self.max_age:
                print(f"🗑️ Scartato messaggio vecchio su {topic} (età: {round(now - t)}s)")
                continue
            try:
                result = self.client.publish(topic, payload, retain=retain)
                if result.rc == 0:
                    print(f"✅ Retry riuscito per {topic}")
                else:
                    raise Exception(f"publish returned {result.rc}")
            except Exception as e:
                print(f"🔁 Retry fallito per {topic}: {e}")
                new_buffer.append((t, topic, payload, retain))

        self.buffer = new_buffer

    def flush(self):
        """Forza il retry di tutti i messaggi attualmente in buffer."""
        print(f"🔄 Tentativo di flush del buffer MQTT...")
        self.retry_buffered()

    def status(self):
        """Restituisce una panoramica sullo stato del buffer."""
        return {
            "buffer_size": len(self.buffer),
            "oldest_age": round(time.time() - self.buffer[0][0]) if self.buffer else 0,
        }

    def is_connected(self):
        return self.client.is_connected()

    def publish(self, topic, payload, retain=True):
        """Permette l'uso diretto come client MQTT: usato da SystemTelemetry."""
        return self.client.publish(topic, payload, retain=retain)

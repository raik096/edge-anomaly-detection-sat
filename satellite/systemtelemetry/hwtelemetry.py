import json
import threading
import time
import psutil
import platform

class SystemTelemetry(threading.Thread):
    # Costruttore
    def __init__(self, mqtt_client, topic="hwtelemetry", interval=5):
        threading.Thread.__init__(self)
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.interval = interval
        self.running = True

        self.prev_bytes_sent = 0
        self.prev_bytes_recv = 0
        self.prev_timestamp = time.time()
        print("🔧 Initializing SystemTelemetry Thread...")  # Aggiungi un log

    def get_telemetry(self):
        current_time = time.time()
        interval = current_time - self.prev_timestamp

        # Ottieni i contatori attuali di invio e ricezione dati
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv

        # Calcola il throughput (in KB/s)
        throughput_sent = (bytes_sent - self.prev_bytes_sent) / 1024 / interval  # KB/s
        throughput_recv = (bytes_recv - self.prev_bytes_recv) / 1024 / interval  # KB/s

        data = {
            "cpu_percent": self.safe_get_psutil_data(psutil.cpu_percent),
            "memory_percent": self.safe_get_psutil_data(lambda: psutil.virtual_memory().percent),
            "disk_percent": self.safe_get_psutil_data(lambda: psutil.disk_usage("/").percent),
            "network_throughput_sent_KBps": throughput_sent,
            "network_throughput_recv_KBps": throughput_recv,
            "temperature": self.get_temperature()
        }
        return data

    def safe_get_psutil_data(self, func):
        """Funzione per ottenere dati da psutil in modo sicuro"""
        try:
            return func()
        except Exception as e:
            print(f"❌ Errore nell'ottenere i dati da psutil: {e}")
            return None

    def get_temperature(self):
        """Recupera la temperatura della CPU"""
        try:
            temps = psutil.sensors_temperatures()
            for key in ("cpu-thermal", "coretemp"):
                if key in temps and temps[key]:
                    temps[key][0].current
            return None  # Se la temperatura non è disponibile
        except Exception as e:
            #print(f"❌ Errore nel recuperare la temperatura: {e}")
            return None

    def run(self):
        while self.running:
            try:
                # Verifica la connessione MQTT
                if self.mqtt_client.is_connected():
                    data = self.get_telemetry()
                    payload = json.dumps(data)
                    self.mqtt_client.publish(self.topic, payload)
                    print(f"⚙️ [HWTELEMETRY] Inviato a {self.topic}: {payload}", flush=True)
                else:
                    print("❌ MQTT Client non connesso.", flush=True)
            except Exception as e:
                print(f"❌ Errore nel thread SystemTelemetry: {e}", flush=True)
            time.sleep(self.interval)

    def stop(self):
        self.running = False

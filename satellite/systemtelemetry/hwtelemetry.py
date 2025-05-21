# satellite/systemtelemetry/hwtelemetry.py

import json
import threading
import time
import psutil

def start_telemetry_thread(mqtt_client):
    telemetry_thread = SystemTelemetry(mqtt_client)
    telemetry_thread.start()
    return telemetry_thread

class SystemTelemetry(threading.Thread):
    def __init__(self, mqtt_client, topic="hwtelemetry", interval=5):
        threading.Thread.__init__(self)
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.interval = interval
        self.running = True

        self.prev_bytes_sent = psutil.net_io_counters().bytes_sent
        self.prev_bytes_recv = psutil.net_io_counters().bytes_recv
        self.prev_timestamp = time.time()
        self.mean_prediction_time = None  # ⬅️ Nuova variabile

    def update_prediction_time(self, ms_value):
        self.mean_prediction_time = ms_value

    def safe_get_psutil_data(self, func):
        try:
            return func()
        except Exception as e:
            print(f"❌ Errore psutil: {e}")
            return None

    def get_temperature(self):
        try:
            temps = psutil.sensors_temperatures()
            for key in ("cpu-thermal", "coretemp"):
                if key in temps and temps[key]:
                    return temps[key][0].current
            return None
        except Exception:
            return None

    def get_telemetry(self):
        current_time = time.time()
        interval = current_time - self.prev_timestamp
        net_io = psutil.net_io_counters()

        throughput_sent = (net_io.bytes_sent - self.prev_bytes_sent) / 1024 / interval
        throughput_recv = (net_io.bytes_recv - self.prev_bytes_recv) / 1024 / interval

        self.prev_bytes_sent = net_io.bytes_sent
        self.prev_bytes_recv = net_io.bytes_recv
        self.prev_timestamp = current_time

        return {
            "cpu_percent": self.safe_get_psutil_data(psutil.cpu_percent),
            "memory_percent": self.safe_get_psutil_data(lambda: psutil.virtual_memory().percent),
            "disk_percent": self.safe_get_psutil_data(lambda: psutil.disk_usage("/").percent),
            "network_throughput_sent_KBps": round(throughput_sent, 2),
            "network_throughput_recv_KBps": round(throughput_recv, 2),
            "temperature": self.get_temperature(),
            "mean_prediction_time_ms": self.mean_prediction_time
        }

    def run(self):
        while self.running:
            try:
                if self.mqtt_client.is_connected():
                    data = self.get_telemetry()
                    payload = json.dumps(data)
                    self.mqtt_client.publish(self.topic, payload)
                    print(f"⚙️ [HWTELEMETRY] Inviato a {self.topic}: {payload}", flush=True)
                else:
                    print("❌ MQTT Client non connesso.")
            except Exception as e:
                print(f"❌ Errore nel thread SystemTelemetry: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False

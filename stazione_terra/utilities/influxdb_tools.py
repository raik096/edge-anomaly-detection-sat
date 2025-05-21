from datetime import datetime
from influxdb_client import InfluxDBClient, WriteOptions, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError

client = None
write_api = None

BUCKET = "telemetryDB"
URL = "http://localhost:8086"
ORG = "re"
TOKEN = "cSnWar-Xt_A0UKNvr27YSsw_bkAHXSxEPOa71uhl24qyevhFnoOxtoiVj-the6Cg7pylKi1dYPdelchVY5OqyA=="
ID_SATELLITE = 1

# Va specificato:
# il nome del database: telemetryDB
# il nome del record (?):
# l'org e il token ovviamente:

# --------------- INIZIALIZZAZIONE ---------------

def init_InfluxDB_Client():
    global client, write_api

    try:
        client = InfluxDBClient(url= URL, token=TOKEN, org=ORG)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        return client

    except Exception as e:
        print(f"❌ Errore nell'inizializzazione del client InfluxDB: {e}")
        return None

# ------------------ SCRITTURA ------------------
# si preoccupa di scrivere quello che ha in argomento nel bucket specificato
def send_msg_to_influxDB(measurement, timestamp, data):
    global write_api

    try:
        p = Point(measurement).tag("id_satellite", str(ID_SATELLITE))

        for channel, value in data.items():
            if value is not None:
                p = p.field(channel, value)
        p = p.time(datetime.utcfromtimestamp(timestamp))
        write_api.write(bucket = BUCKET, record = p)
        print(f"✅ Scrittura completata @ {timestamp}: {p}")

    except Exception as e:
        print(f"❌ Errore nella scrittura: {e}")

    # time.sleep(2)

#--------------------- ALERTS ----------------------

def send_anomaly_to_influxDB(timestamp, channel, score, description=""):
    global write_api

    try:
        point = (
            Point("anomalies")
            .tag("id_satellite", str(ID_SATELLITE))
            .tag("channel", channel)
            .field("anomaly", 1)
            .field("score", float(score))
            .field("description", description)
            .time(datetime.utcfromtimestamp(timestamp))
        )

        write_api.write(bucket=BUCKET, record=point)

    except Exception as e:
        print(f"❌ Errore nell'invio alert: {e}")

from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

def send_hwtelemetry_to_influxDB(cpu_percent=None, temperature=None, memory_percent=None,
                                  disk_percent=None, network_throughput_sent_KBps=None,
                                  network_throughput_recv_KBps=None,
                                  mean_prediction_time_ms=None, timestamp=None,
                                  channel=None, description=""):

    global write_api

    try:
        point = Point("hwtelemetry") \
            .tag("host", "satellite1")

        if channel:
            point = point.tag("channel", str(channel))

        if description:
            point = point.tag("description", description)

        # Aggiungi solo i campi non None
        if cpu_percent is not None:
            point = point.field("cpu_percent", float(cpu_percent))
        if temperature is not None:
            point = point.field("temperature", float(temperature))
        if memory_percent is not None:
            point = point.field("memory_percent", float(memory_percent))
        if disk_percent is not None:
            point = point.field("disk_percent", float(disk_percent))
        if network_throughput_sent_KBps is not None:
            point = point.field("network_throughput_sent_KBps", float(network_throughput_sent_KBps))
        if network_throughput_recv_KBps is not None:
            point = point.field("network_throughput_recv_KBps", float(network_throughput_recv_KBps))
        if mean_prediction_time_ms is not None:
            point = point.field("mean_prediction_time_ms", float(mean_prediction_time_ms))

        if timestamp:
            point = point.time(timestamp)

        write_api.write(bucket=BUCKET, record=point)

    except Exception as e:
        print(f"[InfluxDB] Errore nell'invio della telemetria: {e}")

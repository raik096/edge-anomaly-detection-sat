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

def initInfluxDBClient():
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
def writetodb(timestamp, data):
    global write_api

    try:
        p = Point("satellite1").tag("id_satellite", str(ID_SATELLITE))

        for channel, value in data.items():
            if value is not None:
                p = p.field(channel, value)
        p = p.time(datetime.utcfromtimestamp(timestamp))
        write_api.write(bucket = BUCKET, record = p)
        print(f"✅ Scrittura completata @ {timestamp}: {p}")

    except Exception as e:
        print(f"❌ Errore nella scrittura: {e}")

    # time.sleep(2)
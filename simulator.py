import pandas as pd
import json
import socket
import time

# Configuro l'IP e la porta del Raspberry (Edge Device)
EDGE_DEVICE_IP = "127.0.0.1"
EDGE_DEVICE_PORT = 5005
CSV_FILE = "data/segments.csv"

# Creazione del socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Leggi il dataset
df = pd.read_csv(CSV_FILE)

# Converti i timestamp in formato UNIX (secondi)
df["timestamp"] = pd.to_datetime(df["timestamp"]).astype(int) // 10**9  # Da nanosecondi a secondi

# Ordina i dati per timestamp crescente
df = df.sort_values(by="timestamp")

previous_time = None

for _, row in df.iterrows():
    current_time = row["timestamp"]

    # Calcola il delta temporale e simula il tempo reale
    if previous_time is not None:
        delta_t = current_time - previous_time
        if delta_t > 0:
            time.sleep(delta_t)
    # time.sleep(1)

    message = json.dumps({
        "channel": row["channel"],
        "timestamp": int(time.time()),
        #"timestamp": row["timestamp"],
        "value": row["value"]
    }).encode()

    sock.sendto(message, (EDGE_DEVICE_IP, EDGE_DEVICE_PORT))
    print(f"📡 Inviato: {message}")

    previous_time = current_time

sock.close()
print("✅ Trasmissione completata.")

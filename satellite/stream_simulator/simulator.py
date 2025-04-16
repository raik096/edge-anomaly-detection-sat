""" FILE RESPONSABILE NELLA GESTIONE DEI DATI SIMULATI OPS-SAT e NASA

Questo file si preoccupa di raccogliere, leggendo i dati dalle sorgenti CSV, i valori
corrispondenti ai canali, crea una dataframe sfruttando pandas e legge l'intero file,
accedendo al campo dataframe["timestamp"] modifico il tipo della data portandolo in formato
UNIX in secondi, ordino il dataframe in base al timestamp, e leggo riga per riga,
trasmettendo tramite protocollo vanilla-UDP (senza logica ulteriore), l'intero dataset.

I dati vengono serializzati in JSON
    {"channel": stringa,
        "timestamp": intero,
        "valore": intero}

# La descrizione dei canali viene omogeneizzata, dove CH1 in OPSSAT sta per CADC0872
# mentre in NASA sta per sensore 1.
# MQTT_TOPICS_OPSSAT = [    <-- MAPPATURA
#     "CADC0872" ==  CH1,
#     "CADC0873" ==  CH2,
#     "CADC0874" ==  CH3,
#     "CADC0884" ==  CH4,
#     "CADC0886" ==  CH5,
#     "CADC0888" ==  CH6,
#     "CADC0890" ==  CH7,
#     "ADC0892" ==   CH8,
#     "CADC0894" ==  CH9
# ]
"""

import os
import numpy as np
import pandas as pd
import json
import socket
import time

# ------ GLOBAL VARIABLES ------

EDGE_DEVICE_IP = "127.0.0.1"
EDGE_DEVICE_PORT = 5005

# ------------------------------

# Creazione del socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#csv_file = "satellite/stream_simulator/data/opssat/segments.csv"
csv_file = "data/opssat/segments.csv"

#csv_dir = "satellite/stream_simulator/data/nasa/test"
csv_dir = "data/nasa/test"

############################################## RO

def read_opssat():

    MQTT_TOPICS_OPSSAT = {
         "CADC0872": "CH1",
         "CADC0873" :  "CH2",
         "CADC0874" :  "CH3",
         "CADC0884" :  "CH4",
         "CADC0886" :  "CH5",
         "CADC0888" :  "CH6",
         "CADC0890" :  "CH7",
         "ADC0892" :   "CH8",
         "CADC0894" :  "CH9" }

    # Leggi il dataset
    df = pd.read_csv(csv_file)
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
            "channel": MQTT_TOPICS_OPSSAT[row["channel"]],
            "timestamp": int(time.time()),
            #"timestamp": row["timestamp"],
            "value": row["value"]
        }).encode()

        sock.sendto(message, (EDGE_DEVICE_IP, EDGE_DEVICE_PORT))
        print(f"📡 Inviato: {message}")

        previous_time = current_time

    sock.close()
    print("✅ Trasmissione completata.")

############################################## RN

def read_nasa():

    npy_files = [f for f in os.listdir(csv_dir) if f.endswith(".npy")]

    # Leggo tutti i file all'interno della cartella test fino ad esaurire
    for file_name in npy_files:

            print(f"📂 Caricato: {file_name}")
            file_path = os.path.join(csv_dir, file_name)
            data = np.load(file_path)
            nonzero_columns = np.where(data.any(axis=0))[0]
            print(nonzero_columns)

            df = pd.DataFrame(data)
            print(df.head())
            for col in nonzero_columns[:9]:
                # proietto i valori delle prime 9 colonne che hanno i valori attivi
                for _, row in df.iterrows():
                    data = row[col]
                    print(f"data: {data}, col: {col}")

                    message = json.dumps({

                        "channel": f"CH{int(col)}",
                        "timestamp": int(time.time()),
                        # "timestamp": row["timestamp"],
                        "value": data
                    }).encode()

                    sock.sendto(message, (EDGE_DEVICE_IP, EDGE_DEVICE_PORT))
                    print(f"📡 Inviato: {message}")
                    time.sleep(1)


if __name__ == "__main__":
    # Creazione del socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    read_opssat()
    #read_nasa()
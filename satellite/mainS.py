import socket
import json
import pandas as pd
import paho.mqtt.client as mqtt
from config import UDP_IP, UDP_PORT, MQTT_PORT, MQTT_BROKER, PREDICTION_LENGTH, MAX_WINDOW_CHRONOS_LENGHT
from satellite.systemtelemetry.hwtelemetry import SystemTelemetry

import os
os.environ["HF_HOME"] = "./models/hf_cache"  # Cache locale dei modelli

from chronos import BaseChronosPipeline
import torch


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🔗 Connected to MQTT Broker!", flush=True)
    else:
        print(f"❌ Failed to connect to MQTT Broker with code {rc}", flush=True)


#def on_publish(client, userdata, mid):
#    print(f"✅ Message {mid} published", flush=True)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
#mqtt_client.on_publish = on_publish

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()  # Avvia il loop MQTT per gestire la connessione e le callback

# Inizializza il thread di telemetry e Avvia il thread
telemetry_thread = SystemTelemetry(mqtt_client)
telemetry_thread.start()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on {UDP_IP}:{UDP_PORT}...", flush=True)

# Creo Chronos pipeline
pipeline = BaseChronosPipeline.from_pretrained(
    "amazon/chronos-bolt-small",
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
# La finestra del contesto che viene aggiornata FIFO
context_window = []
context_tensor_window = torch.zeros(MAX_WINDOW_CHRONOS_LENGHT, dtype=torch.float32)
min_quantile_t = None # Il quantile al tempo t+1 che confronto con il nuovo valore t+1
max_quantile_t = None

#Lista per accumulare le predizioni risultanti
predictions_list = []
BATCH_SIZE = 100  # ad esempio, ogni 100 messaggi scriviamo su CSV


while True:

    try:
        data, addr = sock.recvfrom(1024)
        # sensors telemetry
        payload = json.loads(data.decode())
        channel = payload.get("channel")
        timestamp = payload.get("timestamp")
        value = payload.get("value")

        # ---------------- CHRONOS FORECASTING -------------

        if len(context_window) > MAX_WINDOW_CHRONOS_LENGHT:
            context_window.pop(0)

        context_window.append(value)

        # Solo se i quantili sono già stati calcolati una prima volta
        if min_quantile_t is not None and max_quantile_t is not None:
            if min_quantile_t > value or max_quantile_t < value:
                anomaly = 1
            else:
                anomaly = 0
        else:
            anomaly = 0  # Nessuna previsione ancora
        print(f"🌡 Value: {value} | Range: [{min_quantile_t}, {max_quantile_t}] | Anomaly: {anomaly}")

# ------------------------------- BENCHMARK -----------------------
        # Accumula il risultato nella lista
        predictions_list.append({
            "timestamp": timestamp,
            "value": value,
            "min_quantile": min_quantile_t,
            "max_quantile": max_quantile_t,
            "anomaly_pred": anomaly,
            # Se disponi di ground truth in payload, potresti aggiungerla ad esempio:
            # "anomaly_gt": payload.get("anomaly_gt")
        })

        # Se raggiungiamo il batch size, salviamo su CSV e, eventualmente, calcoliamo metriche
        if len(predictions_list) >= BATCH_SIZE:
            predictions_df = pd.DataFrame(predictions_list)
            csv_path = "predictions.csv"
            predictions_df.to_csv(csv_path, index=False)
            print(f"📄 Salvato batch di {BATCH_SIZE} messaggi su {csv_path}")

            # (Opzionale) Se disponi di ground truth, qui potresti richiamare una funzione per calcolare metriche
            # oppure eseguire il benchmark tramite la classe ChronosBenchmark modificata per CSV.
            # Ad esempio:
            from benchmark.chron_benchmark_opssat import ChronosBenchmark
            benchmark = ChronosBenchmark(
                ground_truth_csv="/Users/re/PyCharmMiscProject/satellite/stream_simulator/data/opssat/segments.csv",
                predictions_csv=csv_path,
                channel=channel,)


            results = benchmark.run()
            print("Benchmark results:", results)

            # Dopo l'elaborazione, svuota la lista (oppure accumula ulteriormente se preferisci)
            predictions_list = []
# -------------------------------------------------------------------------

        context_tensor_window = torch.cat([context_tensor_window[1:], torch.tensor([value], dtype=torch.float32)])
        quantiles, mean = pipeline.predict_quantiles(
            context=context_tensor_window,
            prediction_length=12,
            quantile_levels=[0.1, 0.5, 0.9],
        )
        # print("Quantiles shape:", quantiles.shape)
        # print("Quantiles:", quantiles)
        # print("Has NaN:", torch.isnan(quantiles).any())
        # Adesso la tecnica adottata è il rilevamento dell'anomalia sul primo dato previsto, niente di più
        max_quantile_t = quantiles[0, 0, 2].item() # Aggiorno il quantile al tempo t+1
        min_quantile_t = quantiles[0, 0, 0].item()

        # -----------------------------------------------------------
        # plotting.plotting_quantiles(context_window, quantiles)

        if channel and timestamp and value is not None:
            mqtt_topic = f"sensori/{channel}"
            # 0 se è non c'è l'anomalia e 1 se invece c'è
            mqtt_message = json.dumps({
                "timestamp": timestamp,
                "value": value,
                "anomaly": anomaly,})

            mqtt_client.publish(mqtt_topic, mqtt_message, retain=True)
            print(f"📡 Published to {mqtt_topic}: {mqtt_message}")


    except json.JSONDecodeError:
        print("❌ Errore nel parsing JSON")
    except Exception as e:
        print(f"❌ Errore: {e}")


"""
rimodulare il codice con __init__ dentro ogni cartella e capire meglio
lavorare sul benchmark e avere dei parametri che mi diano l'immagine di come
sta andando il tutto
"""
import os
import json
import torch
import time

from satellite.mqtt import mqtt_handler
from satellite.config import MQTT_PORT, MQTT_BROKER, PLOTTING, MONITORING, STRATEGYMODEL
from satellite.stream_simulator import NasaSource, OpssatSource
#from stazione_terra.utilities import plotting
from systemtelemetry import hwtelemetry
from satellite.channel.channel import Channel
from satellite.models.models_factory import get_model

import sys
print("PYTHONPATH:", sys.path)



LOG_PATH = "benchmark/light_log.csv"
os.makedirs("benchmark", exist_ok=True)

telemetry_thread = None  # Global reference to telemetry

# Variabile per tenere traccia dei tempi di previsione
prediction_times = []

def setup_environment():
    os.environ["HF_HOME"] = "./models/hf_cache"
    if not MONITORING:
        print("🛑 MONITORING disabilitato: MQTT e HW telemetry non inizializzati.")
        return None, None
    transmitter = mqtt_handler.setup_transmitter(MQTT_BROKER, MQTT_PORT)
    telemetry = hwtelemetry.start_telemetry_thread(transmitter)
    return transmitter, telemetry

def setup_detectors():
    return {f"CH{i}": Channel(name=f"CH{i}", strategy=get_model(STRATEGYMODEL)) for i in range(10)}

def process_payload(payload, detectors, transmitter):
    global telemetry_thread, prediction_times

    channel_name = payload.get("channel")
    timestamp = payload.get("timestamp")
    value = float(payload.get("value"))  # garantisce compatibilità

    if channel_name not in detectors:
        print(f"⚠️ Canale {channel_name} non gestito.")
        return

    channel = detectors[channel_name]

    start_time = time.time()
    anomaly = channel.process(payload)
    elapsed_ms = (time.time() - start_time) * 1000

    prediction_times.append(elapsed_ms)
    if len(prediction_times) > 100:
        prediction_times.pop(0)

    mean_prediction_time = round(sum(prediction_times) / len(prediction_times), 2)

    if telemetry_thread:
        telemetry_thread.update_prediction_time(mean_prediction_time)

    detector = channel.strategy

#    if PLOTTING:
#        if detector.quantiles is not None and not torch.isnan(detector.quantiles).any():
#            print(f"[{channel_name}] 🌡 Value: {value:.5f} | Range: [{detector.min_q:.5f}, {detector.max_q:.5f}] | Anomaly: {anomaly}")
#            plotting.plotting_quantiles(detector.context_window, detector.quantiles)
#        else:
#            print(f"[{channel_name}] 🌡 Value: {value:.5f} | Warming up... | Anomaly: {anomaly}")

    if MONITORING:
        mqtt_topic = f"sensori/{channel_name}"
        mqtt_message = json.dumps({
            "timestamp": timestamp,
            "value": value,
            "anomaly": anomaly,
        })
        transmitter.send(channel_name, mqtt_message)
        print(f"📡 Published to {mqtt_topic}: {mqtt_message}")

    if len(detector.predictions_list) == 0:
        channel.log_summary()

def process_stream(source, mqtt_client):
    detectors = setup_detectors()
    for payload in source.stream():
        print(payload)
        try:
            process_payload(payload, detectors, mqtt_client)
        except json.JSONDecodeError:
            print("❌ Errore nel parsing JSON")
        except Exception as e:
            print(f"❌ Errore: {e}")

def main():
    global telemetry_thread
    transmitter, telemetry_thread = setup_environment()
    source = OpssatSource()
    process_stream(source, transmitter)

if __name__ == "__main__":
    main()


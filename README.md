# 🛰️ edge-anomaly-detection-sat

Sistema edge-to-ground per il rilevamento in tempo reale di anomalie nei dati di telemetria satellitare.

Basato su modelli fondazionali come Chronos e TimeGPT, il sistema è progettato per operare in ambienti a risorse limitate con comunicazione asincrona via MQTT, salvataggio su InfluxDB e visualizzazione con Grafana.

![schema architettura](docs/architecture_diagram.png)

---

## 🚀 Funzionalità principali

- Rilevamento di anomalie su serie temporali con modelli ML/AI
- Modalità edge a bordo satellite + modulo a terra
- Supporto per:
  - MQTT (Mosquitto)
  - InfluxDB per lo storage time-series
  - Grafana per visualizzazione e allarmi
- Moduli plug-and-play per benchmarking e strategie di detection

---

## 📦 Installazione

### Requisiti

- Python 3.10+
- Docker (opzionale, per simulazione containerizzata)
- InfluxDB 2.x e Grafana (installati localmente o via container)
- Mosquitto MQTT broker

### Setup rapido

```bash
git clone git@github.com:raik096/edge-anomaly-detection-sat.git
cd edge-anomaly-detection-sat
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

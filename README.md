# 🚀 Edge-Based Anomaly Detection in Satellite Telemetry

**Bachelor's Degree Thesis - University of Pisa** **Author:** Andres Lazzari  
**Academic Year:** 2024/2025  
**Supervisor:** Dr. Vincenzo Lomonaco

---

## 📌 Project Description

This repository contains the code and resources developed for my bachelor's thesis: an edge-based system for *forecasting* and *anomaly detection* on satellite telemetry data.  
The project arises from the need to reduce latency and increase the operational autonomy of satellites by detecting anomalous behaviors locally (on-board) in real-time.

The system is designed to operate in computationally constrained environments (edge computing) and integrates next-generation foundational models, such as **Chronos** and **TimeGPT**, with a complete infrastructure for simulation, visualization, and benchmarking.

![Info System](images/infoSystem.jpg)

---

## ⚙️ System Architecture

The system is divided into two main modules:

- **OnBoard Module (Edge):**
  - Local Forecasting & Anomaly Detection
  - Data simulation from NASA/OPS-SAT channels
  - Strategy Pattern for dynamic model selection
  - Docker containerization for low-power environments

- **OnGround Module (Earth):**
  - Data reception via MQTT
  - Storage in InfluxDB
  - Real-time visualization with Grafana
  - Comparative analysis between models (Chronos, TimeGPT, unsupervised models)

---

## 📊 Benchmarks and Models

Several models were implemented to compare performance in terms of accuracy, F1-score, precision, and recall:

- ✅ **Foundational Models**
  - Chronos (AutoGluon-based)
  - TimeGPT (Nixtla)
  
- ⚙️ **Unsupervised Models**
  - Isolation Forest (IForest)
  - KNN, LOF
  - INNE
  
- 🧠 **Anomaly Detection Strategies**
  - Differences, dynamic thresholds, Z-Score, rolling medians, etc.

All results were saved in CSV format and visualized on Grafana for comparative analysis across multiple channels.

---

## 🛰 Datasets

- **OPS-SAT**: ESA public datasets
- **NASA SMAP**: Multichannel series for testing under real conditions
- **Simulation**: Support for offline testing and repeatable experiments

---

## 🧪 How to Run

> Requirements:
- Python 3.10+
- Docker & Docker Compose
- Libraries: `pandas`, `influxdb-client`, `torch`, `scikit-learn`, `nixtla`, etc.

```bash
git clone [https://github.com/tuo-username/edge-anomaly-detection-sat.git](https://github.com/tuo-username/edge-anomaly-detection-sat.git)
cd edge-anomaly-detection-sat

# Environment setup
pip install -r requirements.txt

# Start simulation and detection
python mainT.py --config config/edge.yaml

# Start Grafana + InfluxDB backend
docker-compose up

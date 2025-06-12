# Immagine base minimale
FROM python:3.9-slim

# Crea un utente non-root
RUN groupadd -g 1000 python && \
    useradd -r -u 1000 -g python -m python

# Variabili ambiente
ENV PYTHONPATH=/app
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV HF_HOME=/app/hf_cache

# Installa solo librerie minime di sistema necessarie
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Directory di lavoro
WORKDIR /app

# Copia requirements e installa Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente
COPY satellite /app/satellite
COPY satellite/data /app/satellite/data

# Crea directory cache Hugging Face e assegna permessi
RUN mkdir -p /app/hf_cache && chown -R python:python /app

# Assegna permessi a tutto il progetto
RUN chown -R python:python /app /home/python

# Passa all’utente non-root
USER python

# Working directory nel codice
WORKDIR /app/satellite

# Entry point per benchmark
#ENTRYPOINT ["python", "-u", "benchmark/grid_bench_edge.py"]
ENTRYPOINT ["python", "-u", "mainS.py"]

# Metadata
LABEL authors="re"

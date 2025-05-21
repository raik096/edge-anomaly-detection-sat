# Immagine base
FROM python:3.9-slim

# Crea un utente e gruppo non-root con home directory
RUN groupadd -g 1000 python && \
    useradd -r -u 1000 -g python -m python

# Aggiunge satellite/ al PYTHONPATH e imposta una cartella scrivibile per matplotlib
ENV PYTHONPATH=/app
ENV MPLCONFIGDIR=/tmp/matplotlib

# Imposta una directory cache Hugging Face scrivibile
ENV HF_HOME=/app/hf_cache

# Installa dipendenze di sistema per compilare pacchetti
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Imposta la working directory
WORKDIR /app

# Copia file di requirements e installa le dipendenze Python
COPY satellite/requirements.txt .
RUN echo "🧪 Contenuto /app/satellite/data/nasa/test" && \
    find /app/satellite/data/nasa/test -name "*.npy" || echo "❌ Nessun file copiato"

RUN pip install --no-cache-dir -r requirements.txt

# Copia il progetto
COPY satellite /app/satellite

# Crea directory Hugging Face cache e assegna permessi
RUN mkdir -p /app/hf_cache && chown -R python:python /app

# Cambia permessi di tutto il progetto all'utente non-root
RUN chown -R python:python /app /home/python

# Passa all'utente non-root
USER python

# Imposta la directory principale del progetto
WORKDIR /app/satellite

# Entry point del container
ENTRYPOINT ["python", "-u", "mainS.py"]

# Metadata
LABEL authors="re"

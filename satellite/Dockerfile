FROM python:3.11-slim

RUN groupadd -g 1000 python && \
    useradd -r -u 1000 -g python python

# Copia requirements.txt e installa le dipendenze
COPY requirements.txt .
RUN pip install -r requirements.txt

# Crea e assegna permessi alla cartella dell'app
RUN mkdir /app && chown python:python /app
WORKDIR /app

# Copia il file Python
COPY mainS.py .

# Espone la porta UDP (es: 5005)
EXPOSE 5005/udp

USER 1000

# Imposta come entrypoint per il container
ENTRYPOINT ["python", "mainS.py"]

LABEL authors="re"

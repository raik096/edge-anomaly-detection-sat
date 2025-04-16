#!/bin/bash

source .venv/bin/activate

# Avvia i processi in background e salva i loro PID
python3 ./satellite/simulator/simulator.py &
PID1=$!
python3 ./stazione_terra/mainT.py &
PID2=$!
python3 ./satellite/mainS.py &
PID3=$!

# Cattura Ctrl+C (SIGINT) e termina tutto
trap "echo '🛑 Interruzione, killo i processi...'; kill $PID1 $PID2 $PID3; exit 0" SIGINT

# Attendi la fine
wait

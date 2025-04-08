import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import utils as st

# /Users/re/Desktop/Database/exp_numbers_data.csv

df = pd.read_csv("/Users/re/Desktop/Database/concentrazioni_endotossine.csv")
# Filtrare solo i tipi che contengono "Urbane"
df_urbane = df[df["Tipo"].str.startswith("Urbane_Polvere")]
df_rurali = df[df["Tipo"].str.startswith("Rurali_Polvere")]

listUP = df_urbane["Concentrazione"].tolist()
listRP = df_rurali["Concentrazione"].tolist()


print(f"Media polveri urbane: {st.mediac(listUP)}")
print(f"Deviazione Standard urbane: {st.devstd(listUP)}")
print(f"Scarto interquantile urbane: {st.k_percentile(listUP, 75) - st.k_percentile(listUP, 25)}")
print(f"Q1: {st.k_percentile(listUP, 25)}")
print(f"Q2: {st.k_percentile(listUP, 50)}")
print(f"Q3: {st.k_percentile(listUP, 75)}")
print(f"Q4: {st.k_percentile(listUP, 100)}")


print(f"Media polveri rurali: {st.mediac(listRP)}")
print(f"Deviazione Standard rurali: {st.devstd(listRP)}")
print(f"Scarto interquantile urbane: {st.k_percentile(listRP, 75) - st.k_percentile(listRP, 25)}")
print(f"Q1: {st.k_percentile(listRP, 25)}")
print(f"Q2: {st.k_percentile(listRP, 50)}")
print(f"Q3: {st.k_percentile(listRP, 75)}")
print(f"Q4: {st.k_percentile(listRP, 100)}")


# Creazione dell'istogramma
plt.figure(figsize=(8, 5))  # Imposta dimensioni della figura
plt.hist(listUP, bins=40, color='blue', edgecolor='black', alpha=0.7)  # Istogramma

# Aggiunta di etichette e titolo
plt.xlabel("Concentrazione")
plt.ylabel("Frequenza")
plt.title("Distribuzione della Concentrazione - Urbane Polvere")
plt.grid(axis='y', linestyle='--', alpha=0.7)  # Aggiunge griglia orizzontale

# Mostra il grafico
plt.show()


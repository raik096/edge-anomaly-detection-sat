import pandas as pd
import utils as utils

xi = [1.8, 1.9, 1.8, 2.4, 5.1, 3.1, 5.5, 5.1, 5.3, 4.9, 3.7, 3.8]
yi = [21, 33.5, 24.6, 40.7, 73.2, 24.9, 40.4, 45.3, 64.0, 62.7, 47.2, 44.3]



# Generiamo dati casuali da una distribuzione normale
# Creiamo l'istogramma

df = pd.read_csv('/Users/re/Desktop/Database/Country-data.csv') # leggo il file csv
xlabel = "total_fer"
ylabel = "life_expec"

# Filtrare solo i tipi che contengono "Urbane"
inc = df[xlabel].tolist()
totf = df[ylabel].tolist()

print(inc)
print(totf)
#inc = inc["income"].tolist()
#totf = totf["df"].tolist()

utils.rr(xi, yi)

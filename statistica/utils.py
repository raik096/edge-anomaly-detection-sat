"""
Ecco il mio personalissimo file stats, dove tengo traccia delle
formule apprese in informatica corso di statistica anno 23/24 +
qualche formula di utilità

--> mediac(x), calcola la media
--> medianac(x), calcola la mediana campionaria
--> moda(x), calcola la moda
--> varianc(x), calcola la varianza campionaria
--> scartoqm(x), calcola la deviazione standard
--> skewness(x), colcola l'asimmetria della distribuzione

"""

import matplotlib.pyplot as plt
import numpy as np


# Media campionaria (sensibile ai valori anomali), x è un vettore di numeri
def mediac(x):
    if len(x) == 0: return 0
    tot = 0
    for xi in x:
        tot += xi
    return tot / len(x)


# Mediana campionaria, x vettore di numeri
def medianac(x):
    if len(x) == 0: return 0
    # ordino il vettore
    x = merge_sort(x)
    # ritorno il valore corrispondente all'indice di mezzo
    if (len(x)//2) % 2 == 0:
        return (x[len(x)//2] + x[len(x)//2 + 1]) / 2
    else:
        return x[len(x)+1//2]

# Moda con complessità lineare
def moda(x):
    if not x:
        return None
    contatori = {}
    max_val = x[0]
    max_count = 0

    for num in x:
        if num in contatori:
            contatori[num] += 1
        else:
            contatori[num] = 1
        if contatori[num] > max_count:
            max_count = contatori[num]
            max_val = num

    print(contatori)
    return max_val

#dati = [4, 1, 2, 2, 3, 4, 4, 5, 4, 6]
#print(moda(dati))  # Output: 4

# Varianza campionaria, quindi la dispersione dei dati intorno alla media, x vettore di dati
def varianc(x):
    if not x: return None
    media = mediac(x)
    tot_scarti = 0
    for xi in x:
        tot_scarti += (xi - media)**2
    return tot_scarti/ (len(x)-1)

# Scarto quadratico medio, quindi la varianza ma nell'unità di misura originale
def devstd(x):
    if not x: return None
    return (varianc(x))**(1/2)

# Skewness quindi l'indice di asimmetria
def skewness(x):
    if not x: return None
    media = mediac(x)
    tot_scarti = 0
    for xi in x:
        tot_scarti += (xi - media)**3
    return (tot_scarti/len(x))*(1/devstd(x)**3)

# Ci sarebbe la curtosi ma non la implemento per ora

# Il k percentile, mi indica il valore che fa da spartiacque
# tra il k% dei dati
def k_percentile(x, k):
    if not x: return None
    x = sorted(x)
    num = len(x)
    index = (k / 100) * (num - 1)
    lower_index = int(index)
    upper_index = lower_index + 1
    weight = index - lower_index
    if upper_index < num:
        return x[lower_index] * (1 - weight) + x[upper_index] * weight
    else:
        return x[lower_index]



def outliers(x):
    if not x: return None
    q1 = k_percentile(x, 25)
    q3 = k_percentile(x, 75)
    scarto_interq = q3 - q1
    lim = [q1 - (1.5 * scarto_interq), q3 + (1.5 * scarto_interq)]
    res = []
    for xi in x:
        if xi < lim[0] or xi > lim[1]:
            res.append(xi)
    return res


def covarianza(x, y):
    if not x: return None
    media_x = mediac(x)
    media_y = mediac(y)
    tot = 0
    for i in range(0, len(x)):
        tot += (x[i] - media_x) * (y[i] - media_y)
    return tot / (len(x) - 1)

def coeffDiCorr(x, y):
    if not x: return None
    return covarianza(x, y)/(devstd(x)*devstd(y))

#### FUNZIONE DI PLOT RETTA REGRESSIONE ####
def rr(x, y):
    if not x or not y or len(x) != len(y):
        return None  # Controllo errori

    # Controllo che la deviazione standard non sia nulla
    if varianc(x) == 0 or varianc(y) == 0:
        return None

    # Calcolo dei coefficienti della retta
    b = covarianza(x, y) / varianc(x)
    a = mediac(y) - (b * mediac(x))

    # Retta di regressione basata sui valori reali di x
    x_range = np.linspace(min(x), max(x), 100)  # Usare il range effettivo
    y_range = a + b * x_range

    # Coefficiente di correlazione sui dati originali
    c = coeffDiCorr(x, y)

    # Plot dei dati originali
    plt.scatter(x, y, color='red', label='Dati')
    plt.plot(x_range, y_range, color='blue', label=f"y = {a:.2f} + {b:.2f}x")

    # Titolo e legenda
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title(f"Retta di regressione (Coef. di correlazione: {c:.2f})")
    plt.legend()
    plt.grid()

    plt.show()

############################################


######### FUNZIONE DI PLOT PUNTI ###########
# prende in inputi due vettori, che descrivono gli xi e yi
def plot(x, y):
    if not x or not y: return None
    plt.scatter(x, y, color="red", label="Punti")
    # plt.plot(x, y, linestyle="--", color="gray", alpha=0.5)
    plt.xlabel("x")
    plt.ylabel("y")

    plt.show()
############################################

######### FUNZIONE DI ORDINAMENTO ##########
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    # il // serve per fare frazione parte intera
    # trovo il p.to medio del vettore
    mid = len(arr) // 2

    # divido il vettore in due sotto-vettori
    left_half = merge_sort(arr[:mid])
    left_right = merge_sort(arr[mid:])

    return merge(left_half, left_right)

def merge(left, right):
    sorted_arr = []
    i = j = 0
    # confronto gli elementi delle due metà e inserisce il più piccolo
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            sorted_arr.append(left[i])
            i += 1
        else:
            sorted_arr.append(right[j])
            j += 1

    sorted_arr.extend(left[i:])
    sorted_arr.extend(right[j:])

    return sorted_arr
###########################################

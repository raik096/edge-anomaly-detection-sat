"""I modelli dedicati all anomaly detection:
 - i risultati verranno poi spediti a grafana per gli alert
 - verranno usati due modelli:
    - SUPERVISED: AdaBoostClassifier
    - UNSUPERVISED: IForest
"""

import os
import random
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,precision_score, recall_score, f1_score, roc_auc_score, matthews_corrcoef, average_precision_score
from pyod.utils.data import precision_n_scores
from pyod.models.iforest import IForest
from sklearn.ensemble import AdaBoostClassifier



# Funzione dedicata alla valutazione e calcolo delle metriche con cui valuto il valore, quindi le features!
def evaluate_metrics(y_test, y_pred, y_proba=None, digits=3):
    res = {
            # Calcola quanto accuratamente risponde un sottoinsieme rispetto a y_test
           "Accuracy": round(accuracy_score(y_test, y_pred), digits),
            # Quanto è abile nel non etichettare un falso come vero
           "Precision": round(precision_score(y_test, y_pred), digits),
            # Quanto è abile nel classificare i veri come veri
           "Recall": round(recall_score(y_test, y_pred), digits),
            # La media tra Accuracy e Recall, più vicino ad 1 è meglio è
           "F1": round(f1_score(y_test, y_pred), digits),
            # questo normalizza il risultato sulle classi sbilanciate cioè i diversi tipi di esempi che possono avere size molto diverse,
            # quindi tiene conto dell’accuratezza e della precisione,
            # recall e spicificità, utile quando le classi sono sbilanciate
           "MCC": round(matthews_corrcoef(y_test, y_pred), ndigits=digits)}

    if y_proba is not None:
        # fa una sommatoria degli score di tutti gli esempi, cioè fa una sommatoria
        # su tutti gli n esempi di ∑ (recall n-esimo – recal n-1) * precision n-esimo,
        # quindi è una media pesata sulle precisions raggiunte ad ogni threshold
        res["AUC_PR"] = round(average_precision_score(y_test, y_proba), digits)
        # il grafico che mostra la relazione tra precision e recall, il roc si calcola
        # sulla sua area usando un integrale, il suo scopo è quello di dire
        # quanto il modello sia buono nel distinguere le classi positive da quelle negative
        res["AUC_ROC"] = round(roc_auc_score(y_test, y_proba), digits)
        res["PREC_N_SCORES"] = round(precision_n_scores(y_test, y_proba), digits)
    return res

# Funzione che imposta il seme in modo da poter riprodurre la sequenza di numeri casuali
def set_seed_numpy(seed = 42):
    np.random.seed(seed)
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

features = [
    "mean", "var", "std", "len", "duration", "len_weighted", "gaps_squared", "n_peaks",
    "smooth10_n_peaks", "smooth20_n_peaks", "var_div_duration", "var_div_len",
    "diff_peaks", "diff2_peaks", "diff_var", "diff2_var", "kurtosis", "skew",
]
SEED = 2137

# --------------------- TRAIN FASE ---------------------
# Estraggo dal mio oggetto df, due dataframes, uno che ha valore df.train == e con tutte le features a seguire
# l'altro similmente quelle righe che hanno nel campo train = 1 e con il valore anomaly

df = pd.read_csv("../data/dataset.csv", index_col="segment")

X_train, y_train = df.loc[df.train == 1, features], df.loc[df.train == 1, "anomaly"]
X_test, y_test = df.loc[df.train == 0, features], df.loc[df.train == 0, "anomaly"]
X_train_nominal = df.loc[(df.anomaly == 0)&(df.train == 1), features]

# Pre-processamento dei dati
# standard scaler mi serve per trovare lo z-score ovvero mi serve per
# normalizzare i dati che hanno ordini di grandezza diversi dove nessuna
# feature domina le altre tipo, la media viene normalizzata con il valore 0:
# # [160, 170, 180] -> [-1.22, 0, 1.22], e viene fatta sull training set.

prep = StandardScaler()
X_train_nominal2 = prep.fit_transform(X_train_nominal)
X_train2 = prep.transform(X_train)
X_test2 = prep.transform(X_test)

set_seed_numpy(SEED)

# supervised example

model = AdaBoostClassifier(random_state=SEED)
model.fit(X_train2, y_train)

y_predicted = model.predict(X_test2)
y_predicted_score = model.decision_function(X_test2)

print(model, "\n", evaluate_metrics(y_test, y_predicted, y_predicted_score))

def AdaBoostClassifierPredict(X):

    X2 = prep.transform(X)
    Y = model.predict(X2)
    Y_score = model.decision_function(X2)

    print("⚠️ Anomaly Detected by AdaBoost!" if Y[0] else "✅ All normal. SCORE:" + str(Y_score))

# ------------- OPZIONALE: PLOTTING QUANTILES AND MEAN ------

import matplotlib.pyplot as plt  # requires: pip install matplotlib
import pandas as pd


def plotting_quantiles(context_window, quantiles):
    df = pd.DataFrame(context_window)
    #print(df)
    forecast_index = range(len(df), len(df) + 12)
    low, median, high = quantiles[0, :, 0], quantiles[0, :, 1], quantiles[0, :, 2]

    plt.figure(figsize=(8, 4))
    plt.plot(df, color="royalblue", label="historical data")
    plt.plot(forecast_index, median, color="tomato", label="median forecast")
    plt.fill_between(forecast_index, low, high, color="tomato", alpha=0.3, label="80% prediction interval")
    plt.legend()
    plt.grid()
    plt.show()

# ----------------------------------------------------------
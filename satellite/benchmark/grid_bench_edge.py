import os
import pandas as pd
from itertools import product
from tqdm import tqdm
import more_itertools as mit
from satellite.models.foundational.chronosbolt.chronos.chronos_forecasting import ChronosAnomalyDetector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(ROOT_DIR, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

# ✅ Percorsi file e cartelle
RESULTS_PATH = os.path.join(ROOT_DIR, "satellite/benchmark/results/grid_benchmark_results.csv")
PREDICTIONS_FILE = os.path.join(ROOT_DIR, "satellite/benchmark/predictions.csv")
SEGMENT_PATH = os.path.join(ROOT_DIR, "satellite/data/opssat/segments.csv")
CHRONOS_METRICS_PATH = os.path.join(ROOT_DIR, "satellite/benchmark/chronos_global_metrics.csv")

# ✅ Crea tutte le directory se non esistono
os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PREDICTIONS_FILE), exist_ok=True)
os.makedirs(os.path.dirname(CHRONOS_METRICS_PATH), exist_ok=True)

context_lengths = [48]
prediction_lengths = [1]
quantile_sets = [[0.1, 0.5, 0.9]]
margins = [0.01]
smoothing_opts = [False]
detection_strategies = ["naive"]
model_variants = ["mini"]
normalize_opts = [True]

BATCH_SIZE = 40
CHANNELS = [f"CH{i}" for i in range(5, 10)]
# CHANNELS = [f"CH{i}" for i in range(1, 10)]

if os.path.exists(PREDICTIONS_FILE):
    os.remove(PREDICTIONS_FILE)
if os.path.exists(RESULTS_PATH):
    os.remove(RESULTS_PATH)
if os.path.exists(CHRONOS_METRICS_PATH):
    os.remove(CHRONOS_METRICS_PATH)

def binary_series_to_intervals(binary_array):
    e_seqs = []
    if len(binary_array) > 0:
        groups = [list(group) for group in mit.consecutive_groups(binary_array)]
        e_seqs = [(int(g[0]), int(g[-1])) for g in groups if not g[0] == g[-1]]
    return e_seqs

def compute_segment_metrics(df):
    pred_intervals = binary_series_to_intervals(df["pred_anomaly"].values)
    gt_intervals = binary_series_to_intervals(df["gt_anomaly"].values)

    matched_gt = set()
    tp, fp = 0, 0

    for pred in pred_intervals:
        pred_range = set(range(pred[0], pred[1] + 1))
        overlapping_gt_indices = [
            i for i, gt in enumerate(gt_intervals)
            if len(pred_range & set(range(gt[0], gt[1] + 1))) > 0
        ]
        if overlapping_gt_indices:
            for i in overlapping_gt_indices:
                if i not in matched_gt:
                    matched_gt.add(i)
                    tp += 1
                    break
            else:
                fp += 1
        else:
            fp += 1

    fn = len(gt_intervals) - len(matched_gt)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def run_chronos_benchmark(context_length, prediction_length, quantile_levels, margin, smoothing, strategy, model_variant, normalize):
    df = pd.read_csv(SEGMENT_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["gt_anomaly"] = df["anomaly"]

    channel_map = {
        "CADC0872": "CH1", "CADC0873": "CH2", "CADC0874": "CH3",
        "CADC0884": "CH4", "CADC0886": "CH5", "CADC0888": "CH6",
        "CADC0890": "CH7", "CADC0892": "CH8", "CADC0894": "CH9"
    }

    df["channel"] = df["channel"].map(channel_map)
    df = df[df["channel"].isin(CHANNELS)]

    detectors = {
        ch: ChronosAnomalyDetector(
            model_variant=model_variant,
            batch_size=BATCH_SIZE,
            context_length=context_length,
            prediction_length=prediction_length,
            quantile_levels=quantile_levels,
            margin=margin,
            smoothing=smoothing,
            detection_strategy=strategy,
            normalize=normalize
        ) for ch in CHANNELS
    }

    total_tp = total_fp = total_fn = 0
    results = []

    for ch in tqdm(CHANNELS, desc="Canali"):
        ch_df = df[df["channel"] == ch].copy()
        if len(ch_df) == 0:
            continue

        detector = detectors[ch]
        for _, row in ch_df.iterrows():
            detector.update_context(row["value"], row["timestamp"], ch)
            detector.forecast()
            anomaly = detector.detect_anomaly(row["value"]) if detector.min_q is not None else 0
            detector.accumulate_and_save(row, anomaly)

        pred_df = pd.DataFrame(detector.predictions_list)
        if "gt_anomaly" not in pred_df.columns or "pred_anomaly" not in pred_df.columns:
            continue

        metrics = compute_segment_metrics(pred_df)
        total_tp += metrics["true_positives"]
        total_fp += metrics["false_positives"]
        total_fn += metrics["false_negatives"]

        result_row = {
            "channel": ch,
            "context_length": context_length,
            "prediction_length": prediction_length,
            "quantile": tuple(quantile_levels),
            "margin": margin,
            "smoothing": smoothing,
            "strategy": strategy,
            "model_variant": model_variant,
            "normalize": normalize,
            **metrics
        }
        results.append(result_row)
        pd.DataFrame([result_row]).to_csv(RESULTS_PATH, mode='a', index=False, header=not os.path.exists(RESULTS_PATH))

    if results:
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        global_row = {
            "channel": "ALL",
            "context_length": context_length,
            "prediction_length": prediction_length,
            "quantile": tuple(quantile_levels),
            "margin": margin,
            "smoothing": smoothing,
            "strategy": strategy,
            "model_variant": model_variant,
            "normalize": normalize,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
        pd.DataFrame([global_row]).to_csv(CHRONOS_METRICS_PATH, mode='a', index=False, header=not os.path.exists(CHRONOS_METRICS_PATH))

    return results

if __name__ == "__main__":
    all_results = []
    for ctx_len, pred_len, q_levels, m, s, strategy, variant, normalize in product(
        context_lengths, prediction_lengths, quantile_sets, margins,
        smoothing_opts, detection_strategies, model_variants, normalize_opts
    ):
        print(f"▶️ Config: ctx={ctx_len}, pred={pred_len}, q={q_levels}, margin={m}, smooth={s}, strategy={strategy}, model={variant}, norm={normalize}")
        config_results = run_chronos_benchmark(ctx_len, pred_len, q_levels, m, s, strategy, variant, normalize)
        if config_results:
            all_results.extend(config_results)
            print(f"✅ Salvate {len(config_results)} righe in {RESULTS_PATH}")
        else:
            print("⚠️ Nessun risultato utile per questa configurazione.")

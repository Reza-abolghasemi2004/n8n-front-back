"""
evaluate.py
-----------
Metric computation and plotting helpers.

Everything here takes *predictions/scores* as input, so the same functions
work for Cross-Validation results, out-of-fold predictions, and the final
test set evaluation.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def compute_metrics(y_true, y_pred, y_score=None) -> dict:
    """Accuracy / Precision / Recall / F1 / ROC-AUC in one dict."""
    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
    }
    if y_score is not None:
        metrics["ROC-AUC"] = roc_auc_score(y_true, y_score)
    return metrics


def metrics_table(named_results: dict) -> pd.DataFrame:
    """
    named_results: {model_name: {metric: value}}
    Returns a comparison table sorted by F1.
    """
    table = pd.DataFrame(named_results).T
    return table.round(4).sort_values("F1", ascending=False)


def format_cv_results(cv_results: dict, order=None) -> pd.DataFrame:
    """Convert {metric: (mean, std)} into a one-row DataFrame 'mean ± std'."""
    row = {m: f"{mean:.3f} ± {std:.3f}" for m, (mean, std) in cv_results.items()}
    df = pd.DataFrame([row])
    if order:
        df = df[[c for c in order if c in df.columns]]
    return df


def print_report(y_true, y_pred, title: str = "") -> None:
    if title:
        print(title)
    print(classification_report(y_true, y_pred, target_names=["No Churn", "Churn"], digits=3))


# --------------------------------------------------------------------------- #
# Plots
# --------------------------------------------------------------------------- #
def plot_confusion_matrix(y_true, y_pred, title: str, ax=None):
    """Confusion matrix with raw counts + normalized annotations."""
    cm = confusion_matrix(y_true, y_pred)
    labels = ["No Churn", "Churn"]
    if ax is None:
        _, ax = plt.subplots(figsize=(4.2, 3.6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=labels, yticklabels=labels, ax=ax,
    )
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    # Return normalized values too (each row sums to 1) for interpretation
    row_sums = cm.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    return cm, cm / row_sums


def plot_roc_curves(y_true, named_scores: dict, title: str = "ROC Curve"):
    """Several ROC curves on one axes. named_scores: {name: scores}."""
    plt.figure(figsize=(6.5, 5))
    for name, scores in named_scores.items():
        fpr, tpr, _ = roc_curve(y_true, scores)
        auc = roc_auc_score(y_true, scores)
        plt.plot(fpr, tpr, lw=2, label=f"{name} (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", lw=1, label="Random (AUC = 0.5)")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.title(title)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    return plt.gcf()


def plot_pr_curves(y_true, named_scores: dict, title: str = "Precision-Recall Curve"):
    """Several PR curves on one axes + the no-skill baseline."""
    plt.figure(figsize=(6.5, 5))
    no_skill = np.mean(y_true)
    plt.axhline(no_skill, color="gray", ls="--", lw=1,
                label=f"No-skill (prev = {no_skill:.2f})")
    for name, scores in named_scores.items():
        precision, recall, _ = precision_recall_curve(y_true, scores)
        # Average precision as a single summary number on the legend
        from sklearn.metrics import average_precision_score
        ap = average_precision_score(y_true, scores)
        plt.plot(recall, precision, lw=2, label=f"{name} (AP = {ap:.3f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(title)
    plt.legend(loc="upper right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    return plt.gcf()


def plot_coefficients(feature_names, coefficients, top_n: int = 15, title: str = ""):
    """Horizontal bar chart of the most positive/negative coefficients."""
    coef = pd.Series(coefficients, index=feature_names)
    # Take the top_n with the largest |coefficient|
    top = coef.reindex(coef.abs().sort_values(ascending=False).index).head(top_n)
    top = top.sort_values()

    colors = ["#c0392b" if v < 0 else "#2980b9" for v in top.values]
    plt.figure(figsize=(8, 6))
    top.plot(kind="barh", color=colors)
    plt.xlabel("Coefficient (log-odds impact, scaled features)")
    plt.title(title)
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    return plt.gcf()

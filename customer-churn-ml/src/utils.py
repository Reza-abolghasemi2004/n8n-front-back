"""
utils.py
--------
Utility helpers shared across the project: reproducibility, data loading,
and model persistence.

Everything that should be identical between the notebook and a future
training script lives here, so we never duplicate "infrastructure" code.
"""

from pathlib import Path
import random

import joblib
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Global configuration
# --------------------------------------------------------------------------- #
RANDOM_STATE = 42

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "Telco-Customer-Churn.csv"
MODELS_DIR = PROJECT_ROOT / "models"


def set_global_seed(seed: int = RANDOM_STATE) -> None:
    """Fix seeds for python's `random` and NumPy.

    Note: scikit-learn estimators that have a `random_state` parameter get it
    explicitly in this project (never relying on global seeding alone), which
    is the more robust way to guarantee reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)


def load_dataset(path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Load the Telco Customer Churn CSV into a DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. "
            "See data/README.md for download instructions."
        )
    return pd.read_csv(path)


def save_model(model, name: str) -> Path:
    """Persist a fitted estimator/pipeline with joblib."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    out = MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, out)
    return out


def load_model(name: str):
    """Load a previously saved estimator/pipeline."""
    path = MODELS_DIR / f"{name}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"No saved model called '{name}' in {MODELS_DIR}")
    return joblib.load(path)

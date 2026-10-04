"""
preprocessing.py
----------------
Data cleaning, feature engineering and the sklearn `ColumnTransformer`
used by every model pipeline.

Design decisions (why this file exists at all):
  * Cleaning and feature engineering are pure functions of the raw data,
    so the same code can run in the notebook AND in a future API/training
    script without copy-paste.
  * The ColumnTransformer is *inside* each model's Pipeline, which means
    imputation/scaling/encoding are fit only on the training fold during
    Cross Validation -> no Data Leakage.
"""

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# --------------------------------------------------------------------------- #
# Feature groups (defined once, used everywhere)
# --------------------------------------------------------------------------- #
BASE_NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
BASE_CATEGORICAL_FEATURES = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]

ENGINEERED_NUMERIC_FEATURES = ["AvgMonthlyCharge", "ServicesCount"]

NUMERIC_FEATURES = BASE_NUMERIC_FEATURES + ENGINEERED_NUMERIC_FEATURES
CATEGORICAL_FEATURES = BASE_CATEGORICAL_FEATURES

TARGET_COLUMN = "Churn"
ID_COLUMN = "customerID"

# Columns of add-on services used by `engineer_features`
SERVICE_COLUMNS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]


# --------------------------------------------------------------------------- #
# 1. Cleaning
# --------------------------------------------------------------------------- #
def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning decisions in one place.

    Decisions and their justification:
      * `TotalCharges` is read as object because of 11 empty strings.
        We coerce to numeric -> NaN. The 11 affected customers all have
        tenure == 0 (brand-new customers, nothing billed yet), so we fill
        with 0.0. Filling with the median would invent a billing history
        they don't have; 0 is the factually correct value.
      * Full-row duplicates: none (customerID is unique), but there are
        22 rows identical on every *feature* except the ID. These look like
        genuinely different customers who happen to share the same profile
        (small feature space -> collisions are expected), so we keep them.
        Dropping them would delete real customers from a business dataset.
      * `SeniorCitizen` arrives as 0/1 while every other binary column is
        Yes/No. We convert it to Yes/No so the model treats it consistently
        as a categorical feature (and EDA labels read naturally).
      * We do NOT touch the target here; target encoding happens later.
    """
    out = df.copy()

    # --- TotalCharges: blank strings -> numeric NaN -> 0.0 (tenure == 0) ---
    out["TotalCharges"] = pd.to_numeric(out["TotalCharges"], errors="coerce")
    blank_mask = out["TotalCharges"].isna()
    out.loc[blank_mask, "TotalCharges"] = 0.0

    # --- SeniorCitizen 0/1 -> No/Yes --------------------------------------
    out["SeniorCitizen"] = out["SeniorCitizen"].map({0: "No", 1: "Yes"})

    # --- Exact duplicate rows (all columns, incl. ID) ----------------------
    # customerID is unique, so this is always 0; kept as a safety net.
    out = out.drop_duplicates().reset_index(drop=True)

    return out


def diagnose_issues(df: pd.DataFrame) -> dict:
    """Return a small dict of data-quality facts used in the notebook."""
    total_charges_numeric = pd.to_numeric(df["TotalCharges"], errors="coerce")
    return {
        "n_rows": len(df),
        "n_cols": df.shape[1],
        "duplicate_rows_full": int(df.duplicated().sum()),
        "duplicate_rows_without_id": int(df.drop(columns=[ID_COLUMN]).duplicated().sum()),
        "totalcharges_blank": int(total_charges_numeric.isna().sum()),
        "tenure_zero": int((df["tenure"] == 0).sum()),
        "missing_by_column": df.isna().sum().to_dict(),
    }


# --------------------------------------------------------------------------- #
# 2. Feature engineering
# --------------------------------------------------------------------------- #
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create two new numeric features.

    AvgMonthlyCharge = TotalCharges / tenure
        What the customer *actually* paid per month on average. A customer
        with tenure=0 gets MonthlyCharges (no history to average).
        Why: MonthlyCharges is the *current* price, AvgMonthlyCharge
        captures discounts/hikes accumulated over the whole relationship.

    ServicesCount = number of add-on services the customer uses (0..6)
        Counts 'Yes' across the six optional services.
        Why: bundles signal engagement/switching costs. Customers with
        almost no services are easier to walk away from.

    Leakage check: both are computed only from billing/service history
    that already exists at scoring time. Neither looks at the future nor
    at the target, so they cannot leak label information.
    """
    out = df.copy()

    tenure_safe = out["tenure"].replace(0, np.nan)
    out["AvgMonthlyCharge"] = (out["TotalCharges"] / tenure_safe).fillna(out["MonthlyCharges"])

    out["ServicesCount"] = (out[SERVICE_COLUMNS] == "Yes").sum(axis=1)

    return out


# --------------------------------------------------------------------------- #
# 3. ColumnTransformer
# --------------------------------------------------------------------------- #
def build_preprocessor(
    numeric_features=None,
    categorical_features=None,
) -> ColumnTransformer:
    """
    Numeric pipeline     -> median imputation + StandardScaler
    Categorical pipeline -> most-frequent imputation + OneHotEncoder

    Why scaling matters (short version): KNN and SVM measure *distances*.
    If `TotalCharges` lives in the 0..8000 range and `ServicesCount` in 0..6,
    the big-range feature dominates every distance calculation and the model
    effectively ignores the others. Scaling puts all features on a comparable
    footing. Logistic Regression doesn't *require* scaling to run, but it
    helps optimization converge and makes coefficients comparable.

    OneHotEncoder uses `handle_unknown='ignore'` so that at inference time
    an unseen category (in production) doesn't crash the pipeline.
    `sparse_output=False`: the dataset is tiny (7k rows), dense output keeps
    downstream debugging simpler.
    """
    numeric_features = list(numeric_features or NUMERIC_FEATURES)
    categorical_features = list(categorical_features or CATEGORICAL_FEATURES)

    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_features),
            ("cat", categorical_pipe, categorical_features),
        ],
        remainder="drop",
    )
    return preprocessor

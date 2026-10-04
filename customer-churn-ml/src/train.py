"""
train.py
--------
Model pipelines, Stratified K-Fold Cross Validation and hyperparameter
search helpers.

Every model is wrapped in the SAME structure:

    Pipeline([("preprocess", ColumnTransformer), ("model", estimator)])

so preprocessing is re-fit on every CV fold (no leakage) and the whole
bundle can be saved/served as a single object.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, make_scorer, precision_score, recall_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from src.preprocessing import build_preprocessor

CV_FOLDS = 5

# Metrics reported for every model (not just accuracy — the dataset is
# imbalanced and in churn prediction the cost of errors is asymmetric).
# Custom scorers with zero_division=0 keep the logs clean when a model
# (e.g. the baseline Dummy) predicts no positive samples at all.
SCORING = {
    "accuracy": "accuracy",
    "precision": make_scorer(precision_score, zero_division=0),
    "recall": make_scorer(recall_score, zero_division=0),
    "f1": make_scorer(f1_score, zero_division=0),
    "roc_auc": "roc_auc",
}


def get_cv(n_splits: int = CV_FOLDS, seed: int = 42) -> StratifiedKFold:
    """Stratified K-Fold: every fold keeps the original churn ratio."""
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)


def make_pipeline(estimator) -> Pipeline:
    """Preprocessing + estimator, in one object."""
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            ("model", estimator),
        ]
    )


def make_models(seed: int = 42) -> dict:
    """The three candidate model families with sensible DEFAULT hyperparameters."""
    return {
        "Logistic Regression": make_pipeline(
            LogisticRegression(max_iter=2000, random_state=seed)
        ),
        "KNN": make_pipeline(
            KNeighborsClassifier()
        ),
        "SVM": make_pipeline(
            SVC(kernel="rbf", probability=True, random_state=seed)
        ),
    }


def get_param_grids() -> dict:
    """Search grids keyed by the same names as `make_models`."""
    return {
        "Logistic Regression": {
            # C = inverse regularization strength (see notebook section 11)
            "model__C": [0.01, 0.1, 1.0, 10.0, 100.0],
        },
        "KNN": {
            "model__n_neighbors": [3, 5, 7, 9, 11],
            "model__weights": ["uniform", "distance"],
            "model__p": [1, 2],  # Manhattan vs Euclidean distance
        },
        "SVM": {
            "model__C": [0.1, 1.0, 10.0],
            "model__gamma": ["scale", 0.01],
            "model__kernel": ["rbf", "linear"],
        },
    }


def cross_validate_model(pipeline, X, y, cv=None, scoring=None) -> dict:
    """
    Run Stratified K-Fold CV and return a {metric: (mean, std)} dict.
    Nothing here ever touches the held-out test set.
    """
    cv = cv or get_cv()
    results = cross_validate(
        pipeline, X, y,
        cv=cv,
        scoring=scoring or SCORING,
        n_jobs=-1,
        return_train_score=False,
    )
    return {
        metric: (results[f"test_{metric}"].mean(), results[f"test_{metric}"].std())
        for metric in (scoring or SCORING)
    }


def tune_model(pipeline, param_grid, X, y, cv=None, scoring=None, refit: str = "roc_auc") -> GridSearchCV:
    """
    Exhaustive Grid Search over `param_grid` with Cross Validation.

    We optimize ROC-AUC (threshold-independent) rather than raw accuracy:
    with 73/27 class balance, a model can score 73% accuracy by predicting
    "No" for everyone — accuracy is a lazy objective here.
    All other metrics are still computed for every combination, so we can
    report them for the winning hyperparameters.

    `refit=refit` means after the search the best pipeline (chosen by ROC-AUC)
    is re-fit on the whole training set, ready for evaluation.
    """
    cv = cv or get_cv()
    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring=scoring or SCORING,
        cv=cv,
        n_jobs=-1,
        refit=refit,
        return_train_score=False,
    )
    grid.fit(X, y)
    return grid

"""Training pipeline — stub for v0.2."""

from __future__ import annotations

import pandas as pd


def train(
    df: pd.DataFrame,
    target_column: str,
    *,
    task: str = "auto",
) -> dict[str, object]:
    """Train a model on the given DataFrame. Returns model + metrics.

    This is a stub — full implementation coming in v0.2 with:
    - Auto task detection (classification vs regression)
    - Optuna hyperparameter tuning
    - Multiple algorithm comparison (XGBoost, LightGBM, sklearn)
    - SHAP explanations
    """
    _ = df, target_column, task  # noqa: F841
    return {
        "model": None,
        "metrics": {},
        "status": "not_implemented",
        "message": "Training pipeline coming in v0.2",
    }

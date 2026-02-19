"""Data profiler — column stats, cardinality, nulls."""

from __future__ import annotations

import pandas as pd


def profile_columns(df: pd.DataFrame) -> dict[str, dict[str, object]]:
    """Return detailed stats per column."""
    result: dict[str, dict[str, object]] = {}

    for col in df.columns:
        stats: dict[str, object] = {
            "dtype": str(df[col].dtype),
            "nulls": int(df[col].isna().sum()),
            "null_pct": round(df[col].isna().mean() * 100, 1),
            "unique": int(df[col].nunique()),
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            stats.update({
                "min": float(desc["min"]),
                "max": float(desc["max"]),
                "mean": float(desc["mean"]),
                "median": float(df[col].median()),
                "std": float(desc["std"]),
            })
        elif pd.api.types.is_string_dtype(df[col]):
            top = df[col].value_counts().head(5).to_dict()
            stats["top_values"] = top

        result[col] = stats

    return result


def suggest_target(df: pd.DataFrame) -> list[str]:
    """Suggest likely prediction target columns based on heuristics."""
    candidates: list[str] = []
    for col in df.columns:
        lower = col.lower()
        # Common target column names
        target_hints = [
            "target", "label", "class", "churn", "outcome", "result",
            "price", "sales", "revenue", "predict", "y", "status",
        ]
        if any(hint in lower for hint in target_hints):
            candidates.append(col)

    # Also suggest columns with low cardinality (classification) or numeric (regression)
    if not candidates:
        for col in df.columns:
            unique_ratio = df[col].nunique() / max(len(df), 1)
            if unique_ratio < 0.05 and df[col].nunique() <= 20:
                candidates.append(col)

    return candidates

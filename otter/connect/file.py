"""File loader — CSV, JSON, and Parquet with automatic detection."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load(path: str) -> pd.DataFrame:
    """Load a file into a DataFrame. Auto-detects format by extension."""
    file_path = Path(path).expanduser().resolve()

    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    suffix = file_path.suffix.lower()

    loaders = {
        ".csv": pd.read_csv,
        ".tsv": lambda p: pd.read_csv(p, sep="\t"),
        ".json": pd.read_json,
        ".jsonl": lambda p: pd.read_json(p, lines=True),
        ".parquet": pd.read_parquet,
        ".xlsx": pd.read_excel,
        ".xls": pd.read_excel,
    }

    loader = loaders.get(suffix)
    if loader is None:
        supported = ", ".join(loaders.keys())
        msg = f"Unsupported file type: {suffix}. Supported: {supported}"
        raise ValueError(msg)

    return loader(file_path)


def profile(df: pd.DataFrame) -> str:
    """Generate a readable profile of a DataFrame for AI context."""
    lines: list[str] = []
    lines.append(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n")

    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isna().sum())
        unique = int(df[col].nunique())
        null_pct = f" ({nulls / len(df) * 100:.0f}% missing)" if nulls > 0 else ""

        lines.append(f"  {col} [{dtype}] — {unique:,} unique values{null_pct}")

        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            lines.append(
                f"    min={desc['min']:.2f}  mean={desc['mean']:.2f}  "
                f"max={desc['max']:.2f}  std={desc['std']:.2f}"
            )
        elif pd.api.types.is_string_dtype(df[col]) and unique <= 10:
            top_values = df[col].value_counts().head(5)
            vals = ", ".join(f"{v} ({c})" for v, c in top_values.items())
            lines.append(f"    top: {vals}")

    # Sample rows
    lines.append(f"\nSample (first 3 rows):")
    for _, row in df.head(3).iterrows():
        lines.append(f"  {dict(row)}")

    return "\n".join(lines)

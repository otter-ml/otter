"""Model export — pickle serialization stub."""

from __future__ import annotations

import pickle
from pathlib import Path


def export_pickle(model: object, path: str = "model.pkl") -> Path:
    """Export a trained model to a pickle file.

    Stub — will add ONNX and other formats in v0.2.
    """
    if model is None:
        msg = "No model to export. Train a model first."
        raise ValueError(msg)

    output = Path(path).resolve()
    with output.open("wb") as f:
        pickle.dump(model, f)

    return output

"""Session state for Otter."""

from dataclasses import dataclass, field
from typing import Union

import pandas as pd
from sqlalchemy.engine import Connection


@dataclass
class Session:
    """Holds the current working state for an Otter session."""

    connection: Connection | None = None
    schema_context: str = ""
    trained_model: object = None
    model_metrics: dict[str, float] = field(default_factory=dict)
    conversation: list[dict[str, str]] = field(default_factory=list)
    data: pd.DataFrame | None = None
    data_source: str = ""

    def add_message(self, role: str, content: str) -> None:
        self.conversation.append({"role": role, "content": content})

    def get_context_summary(self) -> str:
        """Build a context string for the AI from current session state."""
        parts: list[str] = []
        if self.schema_context:
            parts.append(f"DATA CONTEXT:\n{self.schema_context}")
        if self.data is not None:
            parts.append(
                f"Loaded DataFrame: {self.data.shape[0]} rows × {self.data.shape[1]} columns"
            )
        if self.trained_model is not None:
            parts.append(f"Trained model metrics: {self.model_metrics}")
        return "\n\n".join(parts)

    def reset(self) -> None:
        self.connection = None
        self.schema_context = ""
        self.trained_model = None
        self.model_metrics = {}
        self.conversation.clear()
        self.data = None
        self.data_source = ""

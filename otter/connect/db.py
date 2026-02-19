"""Database connector — SQLAlchemy-based schema inspection and querying."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine


class DatabaseConnector:
    """Connect to a database, inspect its schema, and run queries."""

    def __init__(self) -> None:
        self._engine: Engine | None = None
        self._connection: Connection | None = None

    def connect(self, connection_string: str) -> Connection:
        """Establish a database connection."""
        self._engine = create_engine(connection_string)
        self._connection = self._engine.connect()
        return self._connection

    def disconnect(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.closed

    def inspect_schema(self) -> dict[str, Any]:
        """Return tables, columns, types, row counts, and sample rows."""
        if self._engine is None or self._connection is None:
            msg = "Not connected to a database"
            raise RuntimeError(msg)

        inspector = inspect(self._engine)
        schema: dict[str, Any] = {}

        for table_name in inspector.get_table_names():
            columns = []
            for col in inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                })

            # Row count
            row_count_result = self._connection.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
            )
            row_count = row_count_result.scalar() or 0

            # Sample rows (first 3)
            sample_result = self._connection.execute(
                text(f"SELECT * FROM {table_name} LIMIT 3")  # noqa: S608
            )
            sample_rows = [dict(row._mapping) for row in sample_result]

            schema[table_name] = {
                "columns": columns,
                "row_count": row_count,
                "sample_rows": sample_rows,
            }

        return schema

    def query(self, sql: str) -> pd.DataFrame:
        """Run a SQL query and return results as a DataFrame."""
        if self._connection is None:
            msg = "Not connected to a database"
            raise RuntimeError(msg)
        return pd.read_sql(text(sql), self._connection)

    def format_schema(self, schema: dict[str, Any] | None = None) -> str:
        """Format the schema as a readable string for AI context."""
        if schema is None:
            schema = self.inspect_schema()

        lines: list[str] = []
        for table_name, info in schema.items():
            lines.append(f"Table: {table_name} ({info['row_count']:,} rows)")
            for col in info["columns"]:
                nullable = " (nullable)" if col["nullable"] else ""
                lines.append(f"  - {col['name']}: {col['type']}{nullable}")
            if info["sample_rows"]:
                lines.append(f"  Sample: {info['sample_rows'][0]}")
            lines.append("")

        return "\n".join(lines)

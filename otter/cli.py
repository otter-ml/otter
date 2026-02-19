"""Otter CLI — Textual chat TUI + typer commands."""

from __future__ import annotations

import re
import sys

import typer
from rich.console import Console

from otter import __version__

console = Console()
app = typer.Typer(
    name="otter",
    help="🦦 Otter — Talk to your data, get ML models",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def default(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """Launch the Otter chat interface."""
    if version:
        console.print(f"otter {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        _launch_tui()


@app.command()
def config() -> None:
    """Show current configuration."""
    from otter.config import Config

    cfg = Config()
    console.print("\n[bold]🦦 Otter Configuration[/bold]\n")
    cfg.show()
    console.print()


def _launch_tui() -> None:
    """Launch the Textual chat application."""
    from otter.tui import OtterApp

    tui = OtterApp()
    tui.run()


def main() -> None:
    app()

"""Provider configuration management for Otter."""

import json
from pathlib import Path
from typing import Literal

from platformdirs import user_config_dir
from rich.console import Console

console = Console()

Provider = Literal["anthropic", "openai", "ollama", "openrouter"]

DEFAULT_MODELS: dict[Provider, str] = {
    "anthropic": "claude-3-5-haiku-20241022",
    "openai": "gpt-4o-mini",
    "ollama": "llama3.2",
    "openrouter": "anthropic/claude-3-haiku",
}

PROVIDER_NAMES: list[Provider] = ["anthropic", "openai", "ollama", "openrouter"]


class Config:
    """Manages Otter configuration stored in ~/.otter/config.json."""

    def __init__(self) -> None:
        self._config_dir = Path(user_config_dir("otter", ensure_exists=True))
        self._config_file = self._config_dir / "config.json"
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._config_file.exists():
            try:
                self._data = json.loads(self._config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                console.print(f"[yellow]Warning: could not read config: {exc}[/yellow]")
                self._data = {}

    def _save(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(
            json.dumps(self._data, indent=2), encoding="utf-8"
        )

    def get_provider(self) -> Provider | None:
        value = self._data.get("provider")
        if value in PROVIDER_NAMES:
            return value  # type: ignore[return-value]
        return None

    def set_provider(self, name: Provider) -> None:
        if name not in PROVIDER_NAMES:
            msg = f"Unknown provider: {name}. Choose from {PROVIDER_NAMES}"
            raise ValueError(msg)
        self._data["provider"] = name
        if "model" not in self._data:
            self._data["model"] = DEFAULT_MODELS[name]
        self._save()

    def get_api_key(self) -> str | None:
        return self._data.get("api_key") or None

    def set_api_key(self, key: str) -> None:
        self._data["api_key"] = key
        self._save()

    def get_model(self) -> str | None:
        provider = self.get_provider()
        return self._data.get("model") or (
            DEFAULT_MODELS[provider] if provider else None
        )

    def set_model(self, name: str) -> None:
        self._data["model"] = name
        self._save()

    def show(self) -> None:
        """Display current configuration."""
        provider = self.get_provider() or "(not set)"
        model = self.get_model() or "(not set)"
        key = self.get_api_key()
        key_display = f"{key[:8]}...{key[-4:]}" if key and len(key) > 12 else (key or "(not set)")
        console.print(f"  Provider: [cyan]{provider}[/cyan]")
        console.print(f"  Model:    [cyan]{model}[/cyan]")
        console.print(f"  API Key:  [dim]{key_display}[/dim]")

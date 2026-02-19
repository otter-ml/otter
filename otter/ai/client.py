"""Multi-provider LLM client for Otter."""

from __future__ import annotations

from typing import Generator

from rich.console import Console

from otter.config import Config, Provider

console = Console()


class OtterAI:
    """Unified interface for multiple LLM providers."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def is_configured(self) -> bool:
        provider = self._config.get_provider()
        if provider is None:
            return False
        if provider == "ollama":
            return True  # No API key needed
        return self._config.get_api_key() is not None

    def chat(self, messages: list[dict[str, str]], system: str) -> str:
        """Send messages and return the full response text."""
        provider = self._config.get_provider()
        if provider is None:
            return "I'm not configured yet. Please set up a provider first."

        dispatch = {
            "anthropic": self._chat_anthropic,
            "openai": self._chat_openai,
            "ollama": self._chat_ollama,
            "openrouter": self._chat_openrouter,
        }
        handler = dispatch.get(provider)
        if handler is None:
            return f"Unknown provider: {provider}"

        try:
            return handler(messages, system)
        except KeyboardInterrupt:
            return "(interrupted)"
        except Exception as exc:
            return f"Error talking to {provider}: {exc}"

    def stream(
        self, messages: list[dict[str, str]], system: str
    ) -> Generator[str, None, None]:
        """Stream response tokens. Falls back to non-streaming if unsupported."""
        provider = self._config.get_provider()
        if provider is None:
            yield "I'm not configured yet. Please set up a provider first."
            return

        dispatch = {
            "anthropic": self._stream_anthropic,
            "openai": self._stream_openai,
            "ollama": self._stream_ollama,
            "openrouter": self._stream_openrouter,
        }
        handler = dispatch.get(provider)
        if handler is None:
            yield f"Unknown provider: {provider}"
            return

        try:
            yield from handler(messages, system)
        except KeyboardInterrupt:
            yield "\n(interrupted)"
        except Exception as exc:
            yield f"\nError talking to {provider}: {exc}"

    # ── Anthropic ────────────────────────────────────────────────

    def _chat_anthropic(
        self, messages: list[dict[str, str]], system: str
    ) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._config.get_api_key())
        response = client.messages.create(
            model=self._config.get_model() or "claude-3-5-haiku-20241022",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def _stream_anthropic(
        self, messages: list[dict[str, str]], system: str
    ) -> Generator[str, None, None]:
        import anthropic

        client = anthropic.Anthropic(api_key=self._config.get_api_key())
        with client.messages.stream(
            model=self._config.get_model() or "claude-3-5-haiku-20241022",
            max_tokens=2048,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    # ── OpenAI ───────────────────────────────────────────────────

    def _chat_openai(
        self, messages: list[dict[str, str]], system: str
    ) -> str:
        return self._openai_compat(messages, system, streaming=False)

    def _stream_openai(
        self, messages: list[dict[str, str]], system: str
    ) -> Generator[str, None, None]:
        yield from self._openai_compat(messages, system, streaming=True)  # type: ignore[misc]

    def _openai_compat(
        self,
        messages: list[dict[str, str]],
        system: str,
        *,
        streaming: bool,
        base_url: str | None = None,
    ) -> str | Generator[str, None, None]:
        import openai

        client = openai.OpenAI(
            api_key=self._config.get_api_key(),
            base_url=base_url,
        )
        full_messages = [{"role": "system", "content": system}, *messages]
        model = self._config.get_model() or "gpt-4o-mini"

        if streaming:
            def _gen() -> Generator[str, None, None]:
                stream = client.chat.completions.create(
                    model=model, messages=full_messages, max_tokens=2048, stream=True
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
            return _gen()

        response = client.chat.completions.create(
            model=model, messages=full_messages, max_tokens=2048
        )
        return response.choices[0].message.content or ""

    # ── OpenRouter ───────────────────────────────────────────────

    def _chat_openrouter(
        self, messages: list[dict[str, str]], system: str
    ) -> str:
        return self._openai_compat(
            messages, system, streaming=False, base_url="https://openrouter.ai/api/v1"
        )

    def _stream_openrouter(
        self, messages: list[dict[str, str]], system: str
    ) -> Generator[str, None, None]:
        result = self._openai_compat(
            messages, system, streaming=True, base_url="https://openrouter.ai/api/v1"
        )
        yield from result  # type: ignore[misc]

    # ── Ollama ───────────────────────────────────────────────────

    def _chat_ollama(
        self, messages: list[dict[str, str]], system: str
    ) -> str:
        import ollama as ollama_sdk

        full_messages = [{"role": "system", "content": system}, *messages]
        response = ollama_sdk.chat(
            model=self._config.get_model() or "llama3.2",
            messages=full_messages,
        )
        return response["message"]["content"]

    def _stream_ollama(
        self, messages: list[dict[str, str]], system: str
    ) -> Generator[str, None, None]:
        import ollama as ollama_sdk

        full_messages = [{"role": "system", "content": system}, *messages]
        stream = ollama_sdk.chat(
            model=self._config.get_model() or "llama3.2",
            messages=full_messages,
            stream=True,
        )
        for chunk in stream:
            yield chunk["message"]["content"]

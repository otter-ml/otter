"""Otter TUI — Textual chat application."""

from __future__ import annotations

import re
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Footer, Header, Input, Markdown, Static

from otter import __version__
from otter.ai.client import OtterAI
from otter.ai.prompts import SYSTEM_PROMPT
from otter.config import Config, PROVIDER_NAMES
from otter.session import Session

# ── Action token pattern ─────────────────────────────────────────
ACTION_RE = re.compile(r"\[ACTION:(\w+)(?::(.+?))?\]")

WELCOME = """\
# 🦦 Otter v{version}

**Talk to your data, get predictions.**

I help you turn spreadsheets and databases into ML models — no coding needed.
Try something like:

- *"I have a CSV with customer data, help me predict who will leave"*
- *"Connect to my postgres database"*
- *"Load sales.xlsx and predict next month's revenue"*
""".format(version=__version__)


# ── Chat message widgets ─────────────────────────────────────────


class Prompt(Markdown):
    """A user message bubble."""


class Response(Markdown):
    """An Otter response bubble."""


class SystemMessage(Markdown):
    """A system/status message."""


# ── CSS ──────────────────────────────────────────────────────────

CSS = """\
Screen {
    background: $surface;
}

#chat-view {
    height: 1fr;
    padding: 1 2;
}

Prompt {
    background: $primary-background;
    color: $text;
    margin: 1 0 0 8;
    padding: 1 2;
}

Response {
    background: $secondary-background;
    color: $text;
    margin: 1 8 0 0;
    padding: 1 2;
}

SystemMessage {
    color: $text-muted;
    margin: 1 4;
    padding: 0 2;
    text-style: italic;
}

#input-bar {
    dock: bottom;
    padding: 1 2;
}
"""


class OtterApp(App[None]):
    """The main Otter chat application."""

    TITLE = "🦦 Otter"
    CSS = CSS
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear chat", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._config = Config()
        self._ai = OtterAI(self._config)
        self._session = Session()
        self._setup_pending = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="chat-view")
        yield Input(placeholder="Ask me anything about your data...", id="input-bar")
        yield Footer()

    async def on_mount(self) -> None:
        chat = self.query_one("#chat-view", VerticalScroll)
        welcome = Response(WELCOME)
        await chat.mount(welcome)
        welcome.anchor()

        if not self._ai.is_configured():
            self._setup_pending = True
            msg = SystemMessage(
                "**First-time setup:** Which AI provider do you want to use?\n\n"
                "Type one of: **anthropic**, **openai**, **ollama**, **openrouter**"
            )
            await chat.mount(msg)
            msg.anchor()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return

        input_widget = self.query_one("#input-bar", Input)
        input_widget.value = ""

        if user_text.lower() in ("exit", "quit"):
            self.exit()
            return

        chat = self.query_one("#chat-view", VerticalScroll)

        # Show user message
        prompt = Prompt(f"**You:** {user_text}")
        await chat.mount(prompt)
        prompt.anchor()

        # Handle setup flow
        if self._setup_pending:
            await self._handle_setup(user_text)
            return

        # Normal conversation
        self._session.add_message("user", user_text)
        self._stream_response()

    async def _handle_setup(self, text: str) -> None:
        """Handle the interactive first-time setup flow."""
        chat = self.query_one("#chat-view", VerticalScroll)

        # Step 1: Provider selection
        if self._config.get_provider() is None:
            text_lower = text.lower().strip()
            if text_lower not in PROVIDER_NAMES:
                msg = SystemMessage(
                    f"I don't recognize **{text}**. "
                    f"Please pick one of: {', '.join(f'**{p}**' for p in PROVIDER_NAMES)}"
                )
                await chat.mount(msg)
                msg.anchor()
                return

            self._config.set_provider(text_lower)  # type: ignore[arg-type]

            if text_lower == "ollama":
                # No API key needed
                self._setup_pending = False
                msg = SystemMessage(
                    "✅ Set up with **Ollama** (local). "
                    f"Using model **{self._config.get_model()}**.\n\n"
                    "You're all set! What data are you working with?"
                )
                await chat.mount(msg)
                msg.anchor()
                return

            msg = SystemMessage(
                f"Got it — **{text_lower}**. Now paste your API key:"
            )
            await chat.mount(msg)
            msg.anchor()
            return

        # Step 2: API key
        if self._config.get_api_key() is None:
            self._config.set_api_key(text.strip())
            self._setup_pending = False
            model = self._config.get_model()
            msg = SystemMessage(
                f"✅ All set! Using **{self._config.get_provider()}** "
                f"with model **{model}**.\n\n"
                "What data are you working with today?"
            )
            await chat.mount(msg)
            msg.anchor()
            return

    @work(thread=True)
    def _stream_response(self) -> None:
        """Stream AI response in a background thread."""
        context = self._session.get_context_summary()
        system = SYSTEM_PROMPT
        if context:
            system += f"\n\nCURRENT SESSION CONTEXT:\n{context}"

        full_response = ""
        for token in self._ai.stream(self._session.conversation, system):
            full_response += token
            self.call_from_thread(self._update_response, full_response)

        self._session.add_message("assistant", full_response)

        # Check for action tokens
        actions = ACTION_RE.findall(full_response)
        if actions:
            action_name, action_arg = actions[0]
            self.call_from_thread(self._execute_action, action_name, action_arg)

    def _update_response(self, text: str) -> None:
        """Update or create the streaming response widget."""
        chat = self.query_one("#chat-view", VerticalScroll)
        try:
            response = self.query_one("#streaming", Response)
            response.update(f"**🦦 Otter:** {text}")
        except NoMatches:
            response = Response(f"**🦦 Otter:** {text}", id="streaming")
            chat.mount(response)
        response.anchor()

    def _finalize_response(self) -> None:
        """Remove the streaming id so next response gets a fresh widget."""
        try:
            response = self.query_one("#streaming", Response)
            response.id = None
        except NoMatches:
            pass

    def _execute_action(self, action: str, arg: str) -> None:
        """Execute an action token from the AI response."""
        self._finalize_response()
        dispatch = {
            "connect": self._action_connect,
            "analyze": self._action_analyze,
            "train": self._action_train,
            "eval": self._action_eval,
            "export": self._action_export,
        }
        handler = dispatch.get(action)
        if handler:
            handler(arg)

    def _action_connect(self, target: str) -> None:
        """Connect to a database or load a file."""
        chat = self.query_one("#chat-view", VerticalScroll)
        target = target.strip()

        # Check if it's a file path
        path = Path(target).expanduser()
        if path.exists() or any(
            target.endswith(ext) for ext in (".csv", ".xlsx", ".json", ".parquet")
        ):
            try:
                from otter.connect.file import load, profile

                df = load(target)
                self._session.data = df
                self._session.data_source = target
                self._session.schema_context = profile(df)

                msg = SystemMessage(
                    f"📂 Loaded **{path.name}** — "
                    f"{df.shape[0]:,} rows × {df.shape[1]} columns"
                )
                chat.mount(msg)
                msg.anchor()
            except (FileNotFoundError, ValueError, OSError) as exc:
                msg = SystemMessage(f"❌ Could not load file: {exc}")
                chat.mount(msg)
                msg.anchor()
        else:
            # Assume database connection string
            try:
                from otter.connect.db import DatabaseConnector

                connector = DatabaseConnector()
                conn = connector.connect(target)
                self._session.connection = conn
                schema = connector.inspect_schema()
                self._session.schema_context = connector.format_schema(schema)

                table_count = len(schema)
                total_rows = sum(t["row_count"] for t in schema.values())
                msg = SystemMessage(
                    f"🔌 Connected — {table_count} tables, {total_rows:,} total rows"
                )
                chat.mount(msg)
                msg.anchor()
            except Exception as exc:
                msg = SystemMessage(f"❌ Connection failed: {exc}")
                chat.mount(msg)
                msg.anchor()

        # Feed result back to AI
        self._session.add_message(
            "user",
            f"[System: data loaded. Context updated. Acknowledge and suggest next steps.]",
        )
        self._stream_response()

    def _action_analyze(self, _arg: str) -> None:
        """Run data profiling."""
        chat = self.query_one("#chat-view", VerticalScroll)

        if self._session.data is None:
            msg = SystemMessage("⚠️ No data loaded yet.")
            chat.mount(msg)
            msg.anchor()
            return

        from otter.analyze.profiler import suggest_target

        suggestions = suggest_target(self._session.data)
        hint = ""
        if suggestions:
            hint = f" Likely prediction targets: **{', '.join(suggestions)}**"

        msg = SystemMessage(f"📊 Analysis complete.{hint}")
        chat.mount(msg)
        msg.anchor()

        self._session.add_message(
            "user",
            f"[System: analysis complete. Target suggestions: {suggestions}. "
            f"Guide the user on what to predict.]",
        )
        self._stream_response()

    def _action_train(self, target_column: str) -> None:
        """Train a model (stub)."""
        chat = self.query_one("#chat-view", VerticalScroll)
        msg = SystemMessage(
            f"🏋️ Training on **{target_column}** — coming in v0.2!"
        )
        chat.mount(msg)
        msg.anchor()

    def _action_eval(self, _arg: str) -> None:
        """Evaluate the trained model (stub)."""
        chat = self.query_one("#chat-view", VerticalScroll)
        msg = SystemMessage("📈 Model evaluation — coming in v0.2!")
        chat.mount(msg)
        msg.anchor()

    def _action_export(self, _arg: str) -> None:
        """Export the trained model (stub)."""
        chat = self.query_one("#chat-view", VerticalScroll)
        msg = SystemMessage("💾 Model export — coming in v0.2!")
        chat.mount(msg)
        msg.anchor()

    def action_clear(self) -> None:
        """Clear the chat history."""
        chat = self.query_one("#chat-view", VerticalScroll)
        chat.remove_children()
        self._session.conversation.clear()
        welcome = Response(WELCOME)
        chat.mount(welcome)
        welcome.anchor()

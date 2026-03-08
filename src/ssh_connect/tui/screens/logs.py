from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import RichLog, Static


class LogsView(Vertical):
    def compose(self):
        yield Static("Logs", classes="title")
        yield RichLog(id="logs-output", wrap=True, highlight=True)

    def append(self, message: str) -> None:
        log = self.query_one("#logs-output", RichLog)
        log.write(message)

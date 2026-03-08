from __future__ import annotations

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static


class HomeView(Vertical):
    def compose(self):
        yield Static("Home", classes="title")
        yield Static("", id="home-summary")
        yield Horizontal(
            Button("Refresh", id="home-refresh", variant="primary"),
            id="home-actions",
        )
        table = DataTable(id="home-checks")
        table.cursor_type = "row"
        yield table

    def on_mount(self) -> None:
        table = self.query_one("#home-checks", DataTable)
        table.add_columns("Check", "Status", "Details")
        self.refresh_view()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "home-refresh":
            self.app.refresh_data()
            self._log("[home] ambiente atualizado")

    def refresh_view(self) -> None:
        summary_text = (
            f"Config: {self.app.config_path}\n"
            f"Keys Dir: {self.app.keys_dir or '~/.ssh'}\n"
            f"Hosts: {len(self.app.hosts)}\n"
            f"Keys: {len(self.app.keys)}\n"
            f"Selected Host: {self.app.selected_host or '-'}\n"
            f"Selected Key: {self.app.selected_key or '-'}"
        )
        self.query_one("#home-summary", Static).update(summary_text)

        checks = [
            ("SSH config", bool(self.app.hosts), "Hosts carregados do arquivo"),
            ("SSH keys", bool(self.app.keys), "Chaves privadas detectadas"),
            ("Host selecionado", bool(self.app.selected_host), "Host ativo para conectar"),
            ("Key selecionada", bool(self.app.selected_key), "Chave ativa para copiar"),
        ]

        table = self.query_one("#home-checks", DataTable)
        table.clear()
        for name, ok, details in checks:
            table.add_row(name, "ok" if ok else "fail", details)

    def _log(self, message: str) -> None:
        if hasattr(self.app, "append_log"):
            self.app.append_log(message)

from __future__ import annotations

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static


class KeysView(Vertical):
    def compose(self):
        yield Static("Keys", classes="title")
        yield Horizontal(
            Button("Refresh", id="keys-refresh", variant="primary"),
            Button("Use Selected Key", id="keys-select", variant="success"),
            id="keys-actions",
        )
        table = DataTable(id="keys-table")
        table.cursor_type = "row"
        yield table
        yield Static("", id="keys-status", classes="status")

    def on_mount(self) -> None:
        table = self.query_one("#keys-table", DataTable)
        table.add_columns("Path", "Selected")
        self.refresh_view()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "keys-refresh":
            self.app.refresh_data()
            self._status("Lista de chaves atualizada")
            self._log("[keys] refresh")
        elif event.button.id == "keys-select":
            self._select_current_key()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "keys-table":
            self._select_current_key()

    def refresh_view(self) -> None:
        table = self.query_one("#keys-table", DataTable)
        table.clear()
        for key_path in self.app.keys:
            selected = "yes" if key_path == self.app.selected_key else ""
            table.add_row(key_path, selected)

        if self.app.selected_key in self.app.keys:
            index = self.app.keys.index(self.app.selected_key)
        else:
            index = 0 if self.app.keys else None
            self.app.selected_key = self.app.keys[0] if self.app.keys else None

        if index is not None:
            table.cursor_coordinate = (index, 0)

        if self.app.selected_key:
            self._status(f"Chave ativa: {self.app.selected_key}")
        else:
            self._status("Nenhuma chave encontrada")

    def _select_current_key(self) -> None:
        if not self.app.keys:
            self._status("Nenhuma chave disponível")
            return

        row_index = self.query_one("#keys-table", DataTable).cursor_row
        if row_index is None or row_index < 0 or row_index >= len(self.app.keys):
            row_index = 0

        self.app.selected_key = self.app.keys[row_index]
        self.refresh_view()
        self._status(f"Chave ativa: {self.app.selected_key}")
        self._log(f"[keys] selected: {self.app.selected_key}")

    def _status(self, text: str) -> None:
        self.query_one("#keys-status", Static).update(text)

    def _log(self, message: str) -> None:
        if hasattr(self.app, "append_log"):
            self.app.append_log(message)

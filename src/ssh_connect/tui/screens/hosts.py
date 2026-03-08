from __future__ import annotations

import asyncio

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static

from src.ssh_connect.services.ssh_service import connect_ssh, copy_ssh_key


class HostsView(Vertical):
    def __init__(self) -> None:
        super().__init__()
        self._visible_hosts: list[str] = []

    def compose(self):
        yield Static("Hosts", classes="title")
        yield Input(placeholder="Filter hosts", id="hosts-filter")
        yield Horizontal(
            Button("Refresh", id="hosts-refresh", variant="primary"),
            Button("Connect", id="hosts-connect", variant="success"),
            Button("Copy Selected Key", id="hosts-copy-key"),
            id="hosts-actions",
        )
        table = DataTable(id="hosts-table")
        table.cursor_type = "row"
        yield table
        yield Static("", id="hosts-details")
        yield Static("", id="hosts-status", classes="status")

    def on_mount(self) -> None:
        table = self.query_one("#hosts-table", DataTable)
        table.add_columns("Host", "HostName", "User", "Comment")
        self.refresh_view()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "hosts-filter":
            self.refresh_view(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "hosts-refresh":
            self.app.refresh_data()
            self._status("Lista de hosts atualizada")
            self._log("[hosts] refresh")
        elif button_id == "hosts-connect":
            self.run_worker(self._connect_selected(), exclusive=True)
        elif button_id == "hosts-copy-key":
            self.run_worker(self._copy_selected_key(), exclusive=True)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "hosts-table":
            return

        host = self._host_at_cursor()
        self.app.selected_host = host
        self._update_details(host)

    def refresh_view(self, filter_text: str = "") -> None:
        filter_value = filter_text.lower().strip()
        self._visible_hosts = [
            host
            for host in self.app.hosts
            if not filter_value or filter_value in host.lower() or filter_value in str(self.app.host_details.get(host, {})).lower()
        ]

        table = self.query_one("#hosts-table", DataTable)
        table.clear()
        for host in self._visible_hosts:
            details = self.app.host_details.get(host, {})
            table.add_row(
                host,
                details.get("HostName", "-"),
                details.get("User", "-"),
                details.get("Comentário", "-"),
            )

        if self.app.selected_host in self._visible_hosts:
            index = self._visible_hosts.index(self.app.selected_host)
        else:
            index = 0 if self._visible_hosts else None
            self.app.selected_host = self._visible_hosts[0] if self._visible_hosts else None

        if index is not None:
            table.cursor_coordinate = (index, 0)

        self._update_details(self.app.selected_host)

    async def _connect_selected(self) -> None:
        host = self._host_at_cursor()
        if not host:
            self._status("Selecione um host")
            return

        self.app.selected_host = host
        self._status(f"Conectando em {host}...")
        self._log(f"[hosts] connect start: {host}")

        try:
            with self.app.suspend():
                await asyncio.to_thread(connect_ssh, host, self.app.config_path, self.app.keys_dir)
            self._status(f"Sessão encerrada para {host}")
            self._log(f"[hosts] connect end: {host}")
        except Exception as exc:
            self._status(f"Falha ao conectar em {host}")
            self._log(f"[hosts] connect error: {exc}")

    async def _copy_selected_key(self) -> None:
        host = self._host_at_cursor()
        if not host:
            self._status("Selecione um host")
            return

        key_path = self.app.selected_key
        if not key_path:
            self._status("Selecione uma chave na aba Keys")
            return

        self.app.selected_host = host
        self._status(f"Copiando chave para {host}...")
        self._log(f"[hosts] copy key start: {host} <- {key_path}")

        try:
            with self.app.suspend():
                await asyncio.to_thread(copy_ssh_key, host, key_path, self.app.config_path)
            self._status(f"Chave copiada para {host}")
            self._log(f"[hosts] copy key end: {host}")
        except Exception as exc:
            self._status(f"Falha ao copiar chave para {host}")
            self._log(f"[hosts] copy key error: {exc}")

    def _host_at_cursor(self) -> str | None:
        if not self._visible_hosts:
            return None

        row_index = self.query_one("#hosts-table", DataTable).cursor_row
        if row_index is None or row_index < 0 or row_index >= len(self._visible_hosts):
            return self._visible_hosts[0]
        return self._visible_hosts[row_index]

    def _update_details(self, host: str | None) -> None:
        if not host:
            details = "Nenhum host disponível."
        else:
            host_info = self.app.host_details.get(host, {})
            details = "\n".join(f"{key}: {value}" for key, value in host_info.items()) or "Nenhuma informação disponível."
        self.query_one("#hosts-details", Static).update(details)

    def _status(self, text: str) -> None:
        self.query_one("#hosts-status", Static).update(text)

    def _log(self, message: str) -> None:
        if hasattr(self.app, "append_log"):
            self.app.append_log(message)

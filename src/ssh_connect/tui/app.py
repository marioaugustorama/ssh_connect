from __future__ import annotations

import os

from src.ssh_connect.services.config_service import host_has_identity_file, parse_ssh_hosts
from src.ssh_connect.services.key_service import list_local_private_keys
from src.ssh_connect.services.ssh_service import connect_ssh, copy_ssh_key

try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Textual não está instalado. Instale a dependência para usar a interface TUI."
    ) from exc


class HostListItem(ListItem):
    """List item that carries the SSH host value."""

    def __init__(self, host: str) -> None:
        super().__init__(Label(host))
        self.host = host


class KeyListItem(ListItem):
    """List item that carries the selected key path."""

    def __init__(self, key_path: str) -> None:
        super().__init__(Label(os.path.basename(key_path)))
        self.key_path = key_path


class KeySelectionScreen(ModalScreen[str | None]):
    """Modal screen used to pick a local private key."""

    CSS = """
    KeySelectionScreen {
        align: center middle;
        background: $background 60%;
    }

    #key-dialog {
        width: 72;
        height: 24;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }

    #key-list {
        height: 1fr;
        border: solid $secondary;
        margin: 1 0;
    }

    #key-actions {
        height: auto;
        align-horizontal: right;
    }

    #key-actions Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancelar"),
        ("q", "dismiss(None)", "Cancelar"),
    ]

    def __init__(self, keys: list[str]) -> None:
        super().__init__()
        self.keys = keys

    def compose(self) -> ComposeResult:
        with Vertical(id="key-dialog"):
            yield Static("Selecione uma chave SSH local", classes="title")
            yield Static("Enter para escolher, Esc para cancelar.")
            yield ListView(*(KeyListItem(key_path) for key_path in self.keys), id="key-list")
            with Horizontal(id="key-actions"):
                yield Button("Cancelar", id="cancel")

    def on_mount(self) -> None:
        key_list = self.query_one("#key-list", ListView)
        if self.keys:
            key_list.index = 0
            key_list.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, KeyListItem):
            self.dismiss(event.item.key_path)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class SSHConnectTextualApp(App[None]):
    """Textual app for browsing hosts and invoking SSH actions."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #host-list {
        width: 40%;
        border: solid $primary;
    }

    #side-panel {
        width: 1fr;
        layout: vertical;
    }

    #details {
        width: 1fr;
        height: 1fr;
        border: solid $secondary;
        padding: 1 2;
    }

    #actions {
        height: auto;
        margin-top: 1;
    }

    #actions Button {
        width: 1fr;
        margin-right: 1;
    }
    """

    TITLE = "SSH Connect"

    BINDINGS = [
        ("enter", "connect", "Conectar"),
        ("f5", "copy_key", "Copiar chave"),
        ("r", "reload", "Recarregar"),
        ("q", "quit", "Sair"),
    ]

    def __init__(self, config_path: str, keys_dir: str | None) -> None:
        super().__init__()
        self.config_path = config_path
        self.keys_dir = keys_dir
        self.hosts: list[str] = []
        self.host_details: dict[str, dict[str, str]] = {}
        self.selected_host: str | None = None
        self._load_hosts()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield ListView(*(HostListItem(host) for host in self.hosts), id="host-list")
            with Vertical(id="side-panel"):
                yield Static("Selecione um host para ver os detalhes.", id="details")
                with Horizontal(id="actions"):
                    yield Button("Conectar", id="connect", variant="primary")
                    yield Button("Copiar chave", id="copy-key")
                    yield Button("Recarregar", id="reload")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = self.config_path
        if self.hosts:
            host_list = self.query_one("#host-list", ListView)
            host_list.index = 0
            host_list.focus()
            self._select_host(self.hosts[0])

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return

        if isinstance(event.item, HostListItem):
            self._select_host(event.item.host)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, HostListItem):
            self.action_connect()

    @on(Button.Pressed, "#connect")
    def press_connect(self) -> None:
        self.action_connect()

    @on(Button.Pressed, "#copy-key")
    def press_copy_key(self) -> None:
        self.action_copy_key()

    @on(Button.Pressed, "#reload")
    def press_reload(self) -> None:
        self.action_reload()

    def action_reload(self) -> None:
        previous_host = self.selected_host
        self._load_hosts()
        self.refresh(recompose=True)
        self.selected_host = previous_host if previous_host in self.hosts else None
        self.set_timer(0, self._restore_selection)

    def action_connect(self) -> None:
        host = self.selected_host
        if not host:
            self.notify("Nenhum host selecionado.", severity="warning")
            return

        try:
            with self.suspend():
                connect_ssh(host, self.config_path, self.keys_dir)
        except Exception as exc:
            self.notify(f"Falha ao conectar: {exc}", title="SSH", severity="error", timeout=8)

    def action_copy_key(self) -> None:
        host = self.selected_host
        if not host:
            self.notify("Nenhum host selecionado.", severity="warning")
            return

        if host_has_identity_file(host, self.config_path):
            self.notify(
                "O host já possui IdentityFile configurado.",
                title="SSH",
                severity="warning",
            )
            return

        keys = list_local_private_keys(self.keys_dir)
        if not keys:
            self.notify("Nenhuma chave SSH encontrada.", title="SSH", severity="error")
            return

        self.push_screen(KeySelectionScreen(keys), callback=self._copy_selected_key)

    def _copy_selected_key(self, selected_key: str | None) -> None:
        if not selected_key or not self.selected_host:
            return

        try:
            with self.suspend():
                copy_ssh_key(self.selected_host, selected_key, self.config_path)
        except Exception as exc:
            self.notify(f"Falha ao copiar chave: {exc}", title="SSH", severity="error", timeout=8)
            return

        self.notify("Chave copiada com sucesso.", title="SSH")
        self.action_reload()

    def _load_hosts(self) -> None:
        self.hosts, self.host_details = parse_ssh_hosts(self.config_path)

    def _restore_selection(self) -> None:
        if not self.hosts:
            self.selected_host = None
            self.query_one("#details", Static).update("Nenhum host encontrado.")
            return

        host = self.selected_host if self.selected_host in self.hosts else self.hosts[0]
        host_list = self.query_one("#host-list", ListView)
        host_index = self.hosts.index(host)
        host_list.index = host_index
        host_list.focus()
        self._select_host(host)

    def _select_host(self, host: str) -> None:
        self.selected_host = host
        self.sub_title = host
        self._update_details(host)

    def _update_details(self, host: str) -> None:
        host_info = self.host_details.get(host, {})
        if not host_info:
            details = "Nenhuma informação disponível"
        else:
            details = "\n".join(f"{key}: {value}" for key, value in host_info.items())

        self.query_one("#details", Static).update(details)

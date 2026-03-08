from __future__ import annotations

from src.ssh_connect.services.config_service import parse_ssh_hosts

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import Footer, Header, ListItem, ListView, Static
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Textual não está instalado. Instale a dependência para usar a interface TUI."
    ) from exc


class SSHConnectTextualApp(App[None]):
    """Primeiro esqueleto de app Textual para futura integração com devops-tools."""

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

    #details {
        width: 1fr;
        border: solid $secondary;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("q", "quit", "Sair"),
    ]

    def __init__(self, config_path: str) -> None:
        super().__init__()
        self.config_path = config_path
        self.hosts, self.host_details = parse_ssh_hosts(config_path)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield ListView(*(ListItem(Static(host)) for host in self.hosts), id="host-list")
            yield Static("Selecione um host para ver os detalhes.", id="details")
        yield Footer()

    def on_mount(self) -> None:
        if self.hosts:
            self.query_one(ListView).index = 0
            self._update_details(self.hosts[0])

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return

        host = str(event.item.query_one(Static).renderable)
        self._update_details(host)

    def _update_details(self, host: str) -> None:
        host_info = self.host_details.get(host, {})
        if not host_info:
            details = "Nenhuma informação disponível"
        else:
            details = "\n".join(f"{key}: {value}" for key, value in host_info.items())

        self.query_one("#details", Static).update(details)

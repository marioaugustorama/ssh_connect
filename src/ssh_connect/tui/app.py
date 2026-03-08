from __future__ import annotations

from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, TabbedContent, TabPane

from src.ssh_connect.services.config_service import parse_ssh_hosts
from src.ssh_connect.services.key_service import list_local_private_keys
from src.ssh_connect.tui.screens.home import HomeView
from src.ssh_connect.tui.screens.hosts import HostsView
from src.ssh_connect.tui.screens.keys import KeysView
from src.ssh_connect.tui.screens.logs import LogsView


class SSHConnectTextualApp(App[None]):
    TITLE = "SSH Connect TUI"
    SUB_TITLE = "Textual"

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-tabs {
        height: 1fr;
    }

    .title {
        text-style: bold;
        padding: 0 0 1 0;
    }

    DataTable {
        height: 1fr;
    }

    .status {
        height: auto;
        padding: 1 0 0 0;
    }

    #logs-output {
        height: 1fr;
        border: heavy $surface;
    }
    """

    def __init__(self, config_path: str, keys_dir: str | None) -> None:
        super().__init__()
        self.config_path = config_path
        self.keys_dir = keys_dir
        self.hosts: list[str] = []
        self.host_details: dict[str, dict[str, str]] = {}
        self.keys: list[str] = []
        self.selected_host: str | None = None
        self.selected_key: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with TabbedContent(id="main-tabs"):
                with TabPane("Home", id="tab-home"):
                    yield HomeView()
                with TabPane("Hosts", id="tab-hosts"):
                    yield HostsView()
                with TabPane("Keys", id="tab-keys"):
                    yield KeysView()
                with TabPane("Logs", id="tab-logs"):
                    yield LogsView()
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()
        self.append_log("SSH Connect TUI iniciada")

    def refresh_data(self) -> None:
        hosts, host_details = parse_ssh_hosts(self.config_path)
        keys = list_local_private_keys(self.keys_dir)

        self.hosts = hosts
        self.host_details = host_details
        self.keys = keys

        if self.selected_host not in self.hosts:
            self.selected_host = self.hosts[0] if self.hosts else None
        if self.selected_key not in self.keys:
            self.selected_key = self.keys[0] if self.keys else None

        for view_type in (HomeView, HostsView, KeysView):
            matches = list(self.query(view_type))
            if matches:
                matches[0].refresh_view()

    def append_log(self, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full = f"[{ts}] {message}"
        logs_view = self.query_one(LogsView)
        logs_view.append(full)


def main(config_path: str, keys_dir: str | None) -> None:
    app = SSHConnectTextualApp(config_path=config_path, keys_dir=keys_dir)
    app.run()

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys

from src.ssh_connect.legacy.curses_ui import run as run_curses_ui
from src.ssh_connect.services.config_service import parse_ssh_hosts
from src.ssh_connect.services.ssh_service import connect_ssh
from src.ssh_connect.tui.app import main as run_textual_ui
from utils import verificar_ou_criar_ssh_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gerenciador de conexões SSH")
    parser.add_argument("-f", "--file", help="Especifica um arquivo de configuração SSH", metavar="CONFIG")
    parser.add_argument("-k", "--keys-dir", help="Especifica um diretório alternativo para as chaves SSH", metavar="KEYS_DIR")
    parser.add_argument(
        "--ui",
        choices=["curses", "textual"],
        default="textual",
        help="Seleciona a interface interativa (padrão: textual; use curses para a interface legada)",
    )
    parser.add_argument("host", nargs="?", help="Nome do host para conexão direta")
    return parser


def resolve_config_path(explicit_path: str | None) -> str:
    return explicit_path if explicit_path else os.path.expanduser("~/.ssh/config")


def resolve_keys_dir(explicit_path: str | None, config_path: str) -> str:
    return explicit_path if explicit_path else os.path.dirname(config_path)


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    config_path = resolve_config_path(args.file)
    keys_dir = resolve_keys_dir(args.keys_dir, config_path)

    verificar_ou_criar_ssh_config(config_path)

    if not os.path.exists(config_path):
        print(f"Erro: O arquivo de configuração '{config_path}' não existe.")
        return 1

    if not os.path.exists(keys_dir):
        print(f"Erro: O diretório de chaves '{keys_dir}' não existe.")
        return 1

    hosts, _ = parse_ssh_hosts(config_path)
    if not hosts:
        print("Nenhum host encontrado.")
        return 1

    if args.host:
        if args.host not in hosts:
            print(f"Erro: O host '{args.host}' não está no arquivo {config_path}")
            return 1

        connect_ssh(args.host, config_path, keys_dir)
        return 0

    if args.ui == "textual":
        try:
            run_textual_ui(config_path=config_path, keys_dir=keys_dir)
            return 0
        except Exception as exc:
            print(f"Textual indisponível ({exc}). Voltando para a interface curses.")

    run_curses_ui(config_path=config_path, keys_dir=keys_dir)
    return 0


def main() -> None:
    try:
        raise SystemExit(run_cli())
    except KeyboardInterrupt:
        print("\nSaindo... (Ctrl+C pressionado)")
        raise SystemExit(0)


if __name__ == "__main__":
    main()

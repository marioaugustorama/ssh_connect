#!/bin/env python3

import os
import re
import curses
import subprocess

def listar_hosts_ssh(config_path=os.path.expanduser("~/.ssh/config")):
    """Lê o arquivo ~/.ssh/config e retorna uma lista de hosts."""
    hosts = []
    try:
        with open(config_path, "r") as f:
            for line in f:
                match = re.match(r"^\s*Host\s+(.+)", line, re.IGNORECASE)
                if match:
                    hosts.extend(match.group(1).split())  # Pode ter múltiplos hosts na mesma linha
    except FileNotFoundError:
        print(f"Arquivo {config_path} não encontrado.")
    return hosts

def menu_navegavel(stdscr, hosts):
    stdscr.clear()
    altura, largura = stdscr.getmaxyx()

    # Título centralizado
    titulo = "Selecione um host para conectar"
    x_titulo = max(0, (largura - len(titulo)) // 2)
    stdscr.addstr(1, x_titulo, titulo, curses.A_BOLD)

    # Limita a quantidade de hosts exibidos para caber na tela
    max_hosts_visiveis = min(len(hosts), altura - 5)  # -5 para evitar estouro
    start_y = max(2, (altura - max_hosts_visiveis) // 2)  # Evita posição negativa

    cursor = 0
    while True:
        stdscr.clear()
        stdscr.addstr(1, x_titulo, titulo, curses.A_BOLD)

        for i, host in enumerate(hosts[:max_hosts_visiveis]):
            y = start_y + i
            x = max(0, (largura - len(host)) // 2)

            # Evita erro de saída de tela
            if 0 <= y < altura and 0 <= x < largura:
                if i == cursor:
                    stdscr.addstr(y, x, f"> {host}", curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, f"  {host}")

        stdscr.refresh()
        key = stdscr.getch()

        # Navegação com setas ↑ ↓
        if key == curses.KEY_UP and cursor > 0:
            cursor -= 1
        elif key == curses.KEY_DOWN and cursor < len(hosts) - 1:
            cursor += 1
        elif key == 10:  # ENTER
            return hosts[cursor]

def conectar_ssh(host):
    """Executa o comando SSH para conectar ao host."""
    print(f"\nConectando ao host: {host}...\n")
    subprocess.run(["ssh", host])

if __name__ == "__main__":
    hosts = listar_hosts_ssh()
    if not hosts:
        print("Nenhum host encontrado.")
    else:
        host_escolhido = curses.wrapper(menu_navegavel, hosts)  # Inicia a interface curses
        conectar_ssh(host_escolhido)


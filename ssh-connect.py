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

import curses

def menu_navegavel(stdscr, hosts):
    stdscr.clear()
    altura, largura = stdscr.getmaxyx()

    titulo = "Selecione um host para conectar"
    x_titulo = max(0, (largura - len(titulo)) // 2)

    cursor = 0
    offset = 0  # Define o deslocamento da rolagem

    max_hosts_visiveis = altura - 5  # Número máximo de itens visíveis (-5 evita estouro)

    while True:
        stdscr.clear()
        stdscr.addstr(1, x_titulo, titulo, curses.A_BOLD)

        # Ajusta o deslocamento da lista quando o cursor atinge os limites visíveis
        if cursor < offset:
            offset = cursor
        elif cursor >= offset + max_hosts_visiveis:
            offset = cursor - max_hosts_visiveis + 1

        # Exibe apenas os hosts visíveis
        for i in range(max_hosts_visiveis):
            index = offset + i
            if index >= len(hosts): 
                break  # Evita erro se acabar a lista

            y = 3 + i
            x = max(0, (largura - len(hosts[index])) // 2)

            if index == cursor:
                stdscr.addstr(y, x, f"> {hosts[index]}", curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, f"  {hosts[index]}")

        stdscr.refresh()
        key = stdscr.getch()

        # Navegação com setas ↑ ↓ e controle de rolagem
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


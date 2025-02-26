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

        # Barra de status na parte inferior
        status_text = "[↑/↓] Navegar  [Enter] Conectar  [PgUp/PgDn] Rolar  [Home/End] Início/Fim  [Q/Esc] Sair"
        stdscr.attron(curses.A_REVERSE)  # Inverte as cores para destacar
        stdscr.addstr(altura - 2, 0, status_text[:largura].ljust(largura))  # Preenche toda a linha
        stdscr.attroff(curses.A_REVERSE)

        stdscr.refresh()
        key = stdscr.getch()

        # Navegação com setas ↑ ↓
        if key == curses.KEY_UP and cursor > 0:
            cursor -= 1
        elif key == curses.KEY_DOWN and cursor < len(hosts) - 1:
            cursor += 1

        # Página inteira para cima (Page Up)
        elif key == curses.KEY_PPAGE:
            cursor = max(0, cursor - max_hosts_visiveis)

        # Página inteira para baixo (Page Down)
        elif key == curses.KEY_NPAGE:
            cursor = min(len(hosts) - 1, cursor + max_hosts_visiveis)

        # Ir para o primeiro item (Home)
        elif key == curses.KEY_HOME:
            cursor = 0

        # Ir para o último item (End)
        elif key == curses.KEY_END:
            cursor = len(hosts) - 1
        
        # Selecionar com ENTER
        elif key == 10:  # ENTER
            return hosts[cursor]

        # Sair com Q ou Esc
        elif key in [27, ord('q')]:
            return None


def conectar_ssh(host):
    """Executa o comando SSH para conectar ao host."""
    print(f"\nConectando ao host: {host}...\n")
    subprocess.run(["ssh", host])

if __name__ == "__main__":
    while True:
        hosts = listar_hosts_ssh()
        if not hosts:
            print("Nenhum host encontrado.")
            break

        host_escolhido = curses.wrapper(menu_navegavel, hosts)
        
        if not host_escolhido:
            break  # Sai do programa se o usuário pressionar Q ou Esc
        
        conectar_ssh(host_escolhido)

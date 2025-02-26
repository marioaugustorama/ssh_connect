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
    """Cria um menu interativo com box para selecionar um host."""
    stdscr.clear()
    altura, largura = stdscr.getmaxyx()

    titulo = "Selecione um host para conectar"
    x_titulo = max(0, (largura - len(titulo)) // 2)

    cursor = 0
    offset = 0  # Define o deslocamento da rolagem
    max_hosts_visiveis = altura - 8  # Ajuste para caber dentro do box

    # Define o tamanho da caixa
    box_altura = max_hosts_visiveis + 2  # Altura suficiente para mostrar os hosts
    box_largura = min(50, largura - 4)  # Largura do box (ajustável)
    box_y = (altura - box_altura) // 2
    box_x = 2

    while True:
        stdscr.clear()
        stdscr.addstr(1, x_titulo, titulo, curses.A_BOLD)

        # Criar uma subjanela (window) dentro do terminal para o box
        box_win = stdscr.subwin(box_altura, box_largura, box_y, box_x)
        box_win.box()  # Desenha a borda ao redor do menu

        # Ajusta o deslocamento da lista
        if cursor < offset:
            offset = cursor
        elif cursor >= offset + max_hosts_visiveis:
            offset = cursor - max_hosts_visiveis + 1

        # Exibe apenas os hosts visíveis dentro do box
        for i in range(max_hosts_visiveis):
            index = offset + i
            if index >= len(hosts):
                break

            y = box_y + 1 + i  # Dentro do box
            x = box_x + 2  # Ajusta para dentro da borda

            if index == cursor:
                stdscr.addstr(y, x, f"> {hosts[index]}", curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, f"  {hosts[index]}")

        # Barra de status fixa na parte inferior
        status_text = "[↑/↓] Navegar  [Enter] Conectar  [PgUp/PgDn] Rolar  [Home/End] Início/Fim  [Q/Esc] Sair"
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(altura - 2, 0, status_text[:largura].ljust(largura))
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

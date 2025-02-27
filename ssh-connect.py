#!/bin/env python3

import os
import re
import sys
import curses
import subprocess
import argparse
import tempfile
from collections import defaultdict


SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")

def listar_hosts_ssh():
    """Lê o arquivo de configuracao e retorna uma lista de hosts e seus detalhes, incluindo comentários."""
    if not os.path.exists(config_path):
        print(f"Erro: O arquivo de configuração '{config_path} não existe.")
        sys.exit(1)

    config_data = defaultdict(dict)
    hosts = []
    comentario_atual = None  # Armazena o comentário antes do host correspondente

    with open(config_path, "r") as f:
        host_atual = None

        for linha in f:
            linha = linha.strip()
            
            # Se for um comentário (## Algo sobre este host), armazena
            if linha.startswith("##"):
                comentario_atual = linha[2:].strip()
            
            elif linha.lower().startswith("host "):  # Definição de um novo host
                host_atual = linha.split(maxsplit=1)[1]
                hosts.append(host_atual)
                config_data[host_atual] = {}
                
                # Se havia um comentário antes, associamos ao host
                if comentario_atual:
                    config_data[host_atual]["Comentário"] = comentario_atual
                    comentario_atual = None  # Resetar para o próximo host
            
            elif host_atual and " " in linha:
                chave, valor = linha.split(maxsplit=1)
                if chave != "#": # Ignora linhas iniciadas com #
                    config_data[host_atual][chave] = valor

    return hosts, config_data  # Retorna hosts + detalhes

def menu_navegavel(stdscr, hosts, host_details):
    """Cria um menu interativo com comentários."""
    stdscr.clear()
    altura, largura = stdscr.getmaxyx()
    titulo = "Selecione um host para conectar"
    x_titulo = max(0, (largura - len(titulo)) // 2)

    cursor = 0
    offset = 0
    max_hosts_visiveis = altura - 10

    box_altura = max_hosts_visiveis + 2
    box_largura = min(50, largura // 2 - 4)
    box_y = (altura - box_altura) // 2
    box_x = 2

    detalhes_x = box_x + box_largura + 2
    detalhes_largura = largura - detalhes_x - 2
    detalhes_altura = box_altura

    while True:
        stdscr.clear()
        stdscr.addstr(1, x_titulo, titulo, curses.A_BOLD)

        box_win = stdscr.subwin(box_altura, box_largura, box_y, box_x)
        box_win.box()

        detalhes_win = stdscr.subwin(detalhes_altura, detalhes_largura, box_y, detalhes_x)
        detalhes_win.box()
        detalhes_win.addstr(1, 2, "Detalhes do Host:", curses.A_BOLD)

        if cursor < offset:
            offset = cursor
        elif cursor >= offset + max_hosts_visiveis:
            offset = cursor - max_hosts_visiveis + 1

        y = box_y + 1

        for i in range(max_hosts_visiveis):
            index = offset + i
            if index >= len(hosts):
                break

            host = hosts[index]
            x = box_x + 2
            if index == cursor:
                stdscr.addstr(y, x, f"> {host}", curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, f"  {host}")

            y += 1

        host_info = host_details.get(hosts[cursor], {})
        linha_atual = 2

        if not host_info:
            detalhes_win.addstr(linha_atual, 2, "Nenhuma informação disponível")
        else:
            for chave, valor in host_info.items():
                if chave != "Comentário" and linha_atual < detalhes_altura - 1:
                    detalhes_win.addstr(linha_atual, 2, f"{chave}: {valor}")
                    linha_atual += 1

            # Adiciona o comentário no final, se existir
            if "Comentário" in host_info and linha_atual < detalhes_altura - 1:
                detalhes_win.addstr(linha_atual + 1, 2, f"Comentário: {host_info['Comentário']}")

        status_text = f"[↑/↓] Navegar  [Enter] Conectar  [PgUp/PgDn] Rolar  [Home/End] Início/Fim  [Q/Esc] Sair | Hosts: {len(hosts)}"
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(altura - 2, 0, status_text[:largura].ljust(largura))
        stdscr.attroff(curses.A_REVERSE)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and cursor > 0:
            cursor -= 1
        elif key == curses.KEY_DOWN and cursor < len(hosts) - 1:
            cursor += 1
        elif key == curses.KEY_PPAGE:
            cursor = max(0, cursor - max_hosts_visiveis)
        elif key == curses.KEY_NPAGE:
            cursor = min(len(hosts) - 1, cursor + max_hosts_visiveis)
        elif key == curses.KEY_HOME:
            cursor = 0
        elif key == curses.KEY_END:
            cursor = len(hosts) - 1
        elif key == 10:
            return hosts[cursor]
        elif key in [27, ord('q')]:
            return None


def criar_config_temporario(config_path, keys_dir):
    """Cria um arquivo de configuração temporário com os caminhos de `IdentityFile` ajustados."""
    temp_config = tempfile.NamedTemporaryFile(delete=False, mode="w")
    temp_path = temp_config.name

    with open(config_path, "r") as original, open(temp_path, "w") as temp:
        for linha in original:
            if linha.strip().startswith("IdentityFile") and keys_dir:
                _, old_path = linha.split(maxsplit=1)
                filename = os.path.basename(old_path.strip())
                new_path = os.path.join(keys_dir, filename)
                temp.write(f"  IdentityFile {new_path}\n")
            else:
                temp.write(linha)

    return temp_path  # Retorna o caminho do arquivo temporário


def conectar_ssh(host):
    """Mostra a box de conexão, sai do modo curses e inicia o SSH."""
    def _mostrar_mensagem(stdscr):
        """Mostra a box "Conectando ao host..." antes de sair do modo curses."""
        stdscr.clear()
        altura, largura = stdscr.getmaxyx()

        box_altura = 5
        box_largura = len(f"Conectando ao host {host}...") + 6
        box_y = (altura - box_altura) // 2
        box_x = (largura - box_largura) // 2

        msg_win = stdscr.subwin(box_altura, box_largura, box_y, box_x)
        msg_win.box()
        msg_win.addstr(2, 3, f"Conectando ao host {host}...", curses.A_BOLD)

        stdscr.refresh()
        curses.napms(1500)  # Exibe a mensagem por 1,5 segundos antes de fechar

    # Exibe a mensagem antes de sair do modo curses
    curses.wrapper(_mostrar_mensagem)

    # Se um diretório de chaves foi informado, criar um config temporário
    final_config_path = criar_config_temporario(config_path, keys_dir) if keys_dir else config_path

    # Inicia a conexão SSH sem interferência do curses
    ssh_command = ["ssh", "-F", final_config_path, host]
    subprocess.run(ssh_command)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Gerenciador de conexões SSH")
        parser.add_argument("-f", "--file", help="Especifica um arquivo de configuração SSH", required=False, metavar="CONFIG", default=SSH_CONFIG_PATH)
        parser.add_argument("-k", "--keys-dir", help="Especifica um diretório alternativo para as chaves SSH", required=False, metavar="KEYS_DIR")
        parser.add_argument("host", nargs="?", help="Nome do host para conexão direta", default=None)
        args = parser.parse_args()

        config_path = args.file
        keys_dir = args.keys_dir if args.keys_dir else os.path.dirname(config_path) 

        if not os.path.exists(config_path):
            print(f"Erro: O arquivo de configuração '{config_path}' não existe.")
            sys.exit(1)

        if not os.path.exists(keys_dir): 
            print(f"Erro: O diretório de chaves '{keys_dir}' não existe.")
            sys.exit(1)

        hosts, host_details = listar_hosts_ssh()  # Carrega a lista de hosts

        if not hosts:
            print("Nenhum host encontrado.")
            sys.exit(1)

        if args.host:
            host_escolhido = args.host
            if host_escolhido not in hosts:
                print(f"Erro: O host '{host_escolhido}' não está no arquivo ~/.ssh/config.")
                sys.exit(1)

            conectar_ssh(host_escolhido)
            sys.exit(0)  # Sai após a conexão SSH

        # Caso contrário, exibe o menu interativo
        while True:
            host_escolhido = curses.wrapper(menu_navegavel, hosts, host_details)

            if not host_escolhido:
                break  # Sai do programa se o usuário pressionar Q ou Esc

            conectar_ssh(host_escolhido)

            curses.wrapper(menu_navegavel, hosts, host_details)  # Retorna ao menu após sair do SSH

    except KeyboardInterrupt:
        try:
            curses.endwin() 
        except curses.error:
            pass
        print("\nSaindo... (Ctrl+C pressionado)")
        sys.exit(0)

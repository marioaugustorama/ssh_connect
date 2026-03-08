#!/bin/env python3

import os
import sys
import curses
import argparse

from src.ssh_connect.services.config_service import host_has_identity_file, parse_ssh_hosts
from src.ssh_connect.services.ssh_service import connect_ssh as run_ssh_connection
from src.ssh_connect.services.ssh_service import copy_ssh_key as run_copy_ssh_key
from utils import verificar_ou_criar_ssh_config, listar_chaves_locais

def copiar_chave_ssh(stdscr, host, keys_dir, config_path):
    """Permite que o usuário escolha uma chave local e a copie para o host."""
    chaves_locais = listar_chaves_locais(keys_dir)

    if not chaves_locais:
        print(f"Erro: Nenhuma chave SSH encontrada no diretório {keys_dir}")
        return

    # Abre menu interativo para selecionar a chave local
    chave_selecionada = menu_selecionar_chave(stdscr, chaves_locais)

    if not chave_selecionada:
        print("Operação cancelada pelo usuário.")
        return

    # Sai do curses antes de executar o ssh-copy-id
    curses.endwin()
    print(f"Enviando chave {chave_selecionada} para {host}...")

    try:
        run_copy_ssh_key(host, chave_selecionada, config_path)
        print(f"Chave {chave_selecionada} adicionada com sucesso a {host}!")
    except Exception:
        print(f"Erro ao adicionar a chave {chave_selecionada} ao host {host}.")

    # Reinicia o curses após o comando
    stdscr.clear()
    curses.initscr()
    stdscr.refresh()

def menu_lateral(stdscr, hosts, host_details, keys_dir, config_path):
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

        status_text = f"[↑/↓] Navegar  [Enter]  Conectar [F5] Copiar chave [PgUp/PgDn] Rolar  [Home/End] Início/Fim  [Q/Esc] Sair | Hosts: {len(hosts)}"
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
        elif key == curses.KEY_F5:  # F5 para copiar chave
            if not host_has_identity_file(hosts[cursor], config_path):
                copiar_chave_ssh(stdscr, hosts[cursor], keys_dir, config_path)


def menu_selecionar_chave(stdscr, chaves):
    curses.curs_set(0)  # Oculta o cursor
    curses.start_color()
    
    # Definição de cores
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Fundo branco
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Seleção preta

    altura, largura = stdscr.getmaxyx()
    
    # Pegar apenas os nomes das chaves, sem os caminhos
    nomes_chaves = [os.path.basename(chave) for chave in chaves]
    
    largura_menu = max(len(chave) for chave in chaves) + 4
    altura_menu = len(chaves) + 2
    x_inicio = (largura - largura_menu) // 2
    y_inicio = (altura - altura_menu) // 2

    win = curses.newwin(altura_menu, largura_menu, y_inicio, x_inicio)
    win.box()
    win.bkgd(' ', curses.color_pair(1))  # Mantém fundo branco

    selecionado = 0
    win.keypad(True)  # Ativa captura de setas do teclado

    while True:
        for i, nome_chave in enumerate(nomes_chaves):
            if i == selecionado:
                win.attron(curses.color_pair(2))
                win.addstr(i + 1, 2, nome_chave.ljust(largura_menu - 4))
                win.attroff(curses.color_pair(2))
            else:
                win.addstr(i + 1, 2, nome_chave.ljust(largura_menu - 4), curses.color_pair(1))

        win.refresh()
        tecla = win.getch()

        if tecla in (curses.KEY_UP, ord('k')) and selecionado > 0:
            selecionado -= 1
        elif tecla in (curses.KEY_DOWN, ord('j')) and selecionado < len(chaves) - 1:
            selecionado += 1
        elif tecla in [10, 13]:  # Enter
            return chaves[selecionado]
        elif tecla in [27, ord('q')]:  # ESC ou Q para sair
            return None  # Permite sair sem selecionar nada

def conectar_ssh(host, config_path, keys_dir):
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

    run_ssh_connection(host, config_path, keys_dir)


def iniciar_textual(config_path, keys_dir):
    """Inicializa o esqueleto da interface Textual."""
    try:
        from src.ssh_connect.tui.app import SSHConnectTextualApp
    except ImportError as exc:
        print(exc)
        sys.exit(1)

    app = SSHConnectTextualApp(config_path=config_path, keys_dir=keys_dir)
    app.run()


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Gerenciador de conexões SSH")
        parser.add_argument("-f", "--file", help="Especifica um arquivo de configuração SSH", required=False, metavar="CONFIG")
        parser.add_argument("-k", "--keys-dir", help="Especifica um diretório alternativo para as chaves SSH", required=False, metavar="KEYS_DIR")
        parser.add_argument("--ui", choices=["curses", "textual"], default="curses", help="Seleciona a interface interativa")
        parser.add_argument("host", nargs="?", help="Nome do host para conexão direta", default=None)
        args = parser.parse_args()

        config_path = args.file if args.file else os.path.expanduser("~/.ssh/config")
        keys_dir = args.keys_dir if args.keys_dir else os.path.dirname(config_path) 

        SSH_CONFIG_PATH = verificar_ou_criar_ssh_config(config_path)

        if not os.path.exists(config_path):
            print(f"Erro: O arquivo de configuração '{config_path}' não existe.")
            sys.exit(1)

        if not os.path.exists(keys_dir): 
            print(f"Erro: O diretório de chaves '{keys_dir}' não existe.")
            sys.exit(1)

        hosts, host_details = parse_ssh_hosts(config_path)

        if not hosts:
            print("Nenhum host encontrado.")
            sys.exit(1)

        if args.host:
            host_escolhido = args.host
            if host_escolhido not in hosts:
                print(f"Erro: O host '{host_escolhido}' não está no arquivo {config_path}")
                sys.exit(1)

            conectar_ssh(host_escolhido, config_path, keys_dir)
            sys.exit(0)  # Sai após a conexão SSH

        if args.ui == "textual":
            iniciar_textual(config_path, keys_dir)
            sys.exit(0)

        # Caso contrário, exibe o menu interativo
        while True:
            host_escolhido = curses.wrapper(menu_lateral, hosts, host_details, keys_dir, config_path)

            if not host_escolhido:
                break  # Sai do programa se o usuário pressionar Q ou Esc

            conectar_ssh(host_escolhido, config_path, keys_dir)

    except KeyboardInterrupt:
        try:
            curses.endwin() 
        except curses.error:
            pass
        print("\nSaindo... (Ctrl+C pressionado)")
        sys.exit(0)

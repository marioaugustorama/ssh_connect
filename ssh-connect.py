#!/bin/env python3

import os
import sys
import curses
import shlex
import subprocess
import argparse
import tempfile
from collections import defaultdict
from utils import verificar_ou_criar_ssh_config, listar_chaves_locais, obter_host_user

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
        hostname_real, usuario = obter_host_user(host, config_path)
        subprocess.run(["ssh-copy-id", "-i", chave_selecionada, f"{usuario}@{hostname_real}"], check=True)
        print(f"Chave {chave_selecionada} adicionada com sucesso a {host}!")
    except subprocess.CalledProcessError:
        print(f"Erro ao adicionar a chave {chave_selecionada} ao host {host}.")

    # Reinicia o curses após o comando
    stdscr.clear()
    curses.initscr()
    stdscr.refresh()


def verificar_chave_no_config(host, config_path):
    """Verifica se o host já tem uma chave associada no arquivo informado."""
    if not os.path.exists(config_path):
        return False  # Se o arquivo não existir, assume que não há chave

    with open(config_path, "r") as f:
        lines = f.readlines()

    inside_host = False
    for line in lines:
        line = line.strip()
        if line.lower().startswith("host "):
            inside_host = host in line  # Marca se estamos dentro do bloco do host
        elif inside_host and line.lower().startswith("identityfile "):
            return True  # Encontramos uma chave associada a esse host

    return False  # Nenhuma chave encontrada para esse host


def listar_hosts_ssh(config_path):
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
            if not verificar_chave_no_config(hosts[cursor], config_path):
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


def criar_config_temporario(config_path, keys_dir):
    """Cria um arquivo de configuração temporário com os caminhos de `IdentityFile` ajustados."""
    temp_config = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    temp_path = temp_config.name

    with open(config_path, "r", encoding="utf-8") as original, open(temp_path, "w", encoding="utf-8") as temp:
        for linha in original:
            linha_sem_quebra = linha.rstrip("\n")
            stripped = linha_sem_quebra.strip()

            if stripped.lower().startswith("identityfile") and keys_dir:
                indent = linha_sem_quebra[: len(linha_sem_quebra) - len(linha_sem_quebra.lstrip())]
                try:
                    parts = shlex.split(stripped)
                except ValueError:
                    temp.write(linha)
                    continue

                if not parts or parts[0].lower() != "identityfile":
                    temp.write(linha)
                    continue

                novos_caminhos = []
                for caminho in parts[1:]:
                    filename = os.path.basename(caminho)
                    novo_caminho = os.path.join(keys_dir, filename)
                    novos_caminhos.append(shlex.quote(novo_caminho))

                temp.write(f"{indent}IdentityFile {' '.join(novos_caminhos)}\n")
            else:
                temp.write(linha)

    return temp_path  # Retorna o caminho do arquivo temporário


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

    temp_config_path = None
    final_config_path = config_path

    # Se um diretório de chaves foi informado, criar um config temporário
    if keys_dir:
        temp_config_path = criar_config_temporario(config_path, keys_dir)
        final_config_path = temp_config_path

    # Inicia a conexão SSH sem interferência do curses
    ssh_command = ["ssh", "-F", final_config_path, host]
    try:
        subprocess.run(ssh_command)
    finally:
        if temp_config_path and os.path.exists(temp_config_path):
            os.remove(temp_config_path)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Gerenciador de conexões SSH")
        parser.add_argument("-f", "--file", help="Especifica um arquivo de configuração SSH", required=False, metavar="CONFIG")
        parser.add_argument("-k", "--keys-dir", help="Especifica um diretório alternativo para as chaves SSH", required=False, metavar="KEYS_DIR")
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

        hosts, host_details = listar_hosts_ssh(config_path)  # Carrega a lista de hosts

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

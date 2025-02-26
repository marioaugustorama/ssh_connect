#!/bin/env python3
import os
import re
import subprocess

def listar_hosts_ssh(config_path=os.path.expanduser("~/.ssh/config")):
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

def selecionar_host(hosts):
    print("\nSelecione um host para conectar:")
    for idx, host in enumerate(hosts, 1):
        print(f"[{idx}] {host}")

    while True:
        escolha = input("Digite o número do host desejado: ")
        if escolha.isdigit():
            escolha = int(escolha)
            if 1 <= escolha <= len(hosts):
                return hosts[escolha - 1]
        print("Opção inválida. Tente novamente.")

def conectar_ssh(host):
    print(f"\nConectando ao host: {host}...\n")
    subprocess.run(["ssh", host])

if __name__ == "__main__":
    hosts = listar_hosts_ssh()
    if not hosts:
        print("Nenhum host encontrado.")
    else:
        host_escolhido = selecionar_host(hosts)
        conectar_ssh(host_escolhido)


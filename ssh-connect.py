#!/bin/env python3
import os
import re

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

if __name__ == "__main__":
    hosts = listar_hosts_ssh()
    if hosts:
        print("Hosts encontrados:")
        for host in hosts:
            print(f" - {host}")
    else:
        print("Nenhum host encontrado.")


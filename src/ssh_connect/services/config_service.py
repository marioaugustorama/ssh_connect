from __future__ import annotations

import os
import shlex
import tempfile
from collections import defaultdict


def ensure_ssh_config(config_path: str) -> str:
    """Ensure the SSH config file and parent directory exist with safe permissions."""
    ssh_dir = os.path.dirname(config_path)

    try:
        if not os.path.exists(ssh_dir):
            print(f"Criando diretório {ssh_dir}")
            os.makedirs(ssh_dir, mode=0o700)

        if not os.path.exists(config_path):
            print(f"Criando arquivo {config_path}")
            with open(config_path, "w", encoding="utf-8") as config_file:
                config_file.write("# Arquivo de configuração SSH\n")

            os.chmod(config_path, 0o600)
    except PermissionError:
        print(f"Erro: Permissão negada ao criar {config_path}. Tente rodar o programa com sudo.")
        raise SystemExit(1)

    return config_path


def parse_ssh_hosts(config_path: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Read SSH config hosts and collect host details plus leading comments."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"O arquivo de configuração '{config_path}' não existe.")

    config_data: dict[str, dict[str, str]] = defaultdict(dict)
    hosts: list[str] = []
    current_comment = None

    with open(config_path, "r", encoding="utf-8") as config_file:
        current_host = None

        for line in config_file:
            stripped_line = line.strip()

            if stripped_line.startswith("##"):
                current_comment = stripped_line[2:].strip()
            elif stripped_line.lower().startswith("host "):
                current_host = stripped_line.split(maxsplit=1)[1]
                hosts.append(current_host)
                config_data[current_host] = {}

                if current_comment:
                    config_data[current_host]["Comentário"] = current_comment
                    current_comment = None
            elif current_host and " " in stripped_line:
                key, value = stripped_line.split(maxsplit=1)
                if key != "#":
                    config_data[current_host][key] = value

    return hosts, dict(config_data)


def host_has_identity_file(host: str, config_path: str) -> bool:
    """Check whether a host block already contains IdentityFile."""
    if not os.path.exists(config_path):
        return False

    with open(config_path, "r", encoding="utf-8") as config_file:
        inside_host = False

        for line in config_file:
            stripped_line = line.strip()
            if stripped_line.lower().startswith("host "):
                inside_host = host in stripped_line
            elif inside_host and stripped_line.lower().startswith("identityfile "):
                return True

    return False


def get_host_user(host: str, config_path: str | None = None) -> tuple[str, str]:
    """Resolve HostName and User for a host entry from SSH config."""
    if config_path is None:
        config_path = os.path.expanduser("~/.ssh/config")

    hostname = None
    user = "root"
    capturing = False

    if not os.path.exists(config_path):
        print(f"Erro: O arquivo de configuração '{config_path}' não existe.")
        return host, user

    with open(config_path, "r", encoding="utf-8") as config_file:
        for line in config_file:
            stripped_line = line.strip()

            if stripped_line.lower().startswith("host "):
                capturing = host in stripped_line.split()[1:]
                continue

            if capturing:
                if stripped_line.lower().startswith("hostname "):
                    hostname = stripped_line.split()[1]
                elif stripped_line.lower().startswith("user "):
                    user = stripped_line.split()[1]

            if hostname and user:
                break

    return hostname if hostname else host, user


def create_temp_config_with_keys(config_path: str, keys_dir: str | None) -> str:
    """Create a temporary SSH config overriding IdentityFile paths to a target dir."""
    temp_config = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    temp_path = temp_config.name
    temp_config.close()

    with open(config_path, "r", encoding="utf-8") as original, open(temp_path, "w", encoding="utf-8") as temp:
        for line in original:
            line_without_break = line.rstrip("\n")
            stripped_line = line_without_break.strip()

            if stripped_line.lower().startswith("identityfile") and keys_dir:
                indent = line_without_break[: len(line_without_break) - len(line_without_break.lstrip())]
                try:
                    parts = shlex.split(stripped_line)
                except ValueError:
                    temp.write(line)
                    continue

                if not parts or parts[0].lower() != "identityfile":
                    temp.write(line)
                    continue

                new_paths = []
                for path in parts[1:]:
                    filename = os.path.basename(path)
                    new_path = os.path.join(keys_dir, filename)
                    new_paths.append(shlex.quote(new_path))

                temp.write(f"{indent}IdentityFile {' '.join(new_paths)}\n")
            else:
                temp.write(line)

    return temp_path

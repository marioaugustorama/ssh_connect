import os

def verificar_ou_criar_ssh_config():
    """Verifica se ~/.ssh/config existe e cria caso contrário, com permissões corretas."""
    ssh_dir = os.path.expanduser("~/.ssh")
    config_path = os.path.join(ssh_dir, "config")

    try:
        if not os.path.exists(ssh_dir):
            print(f"Criando diretório {ssh_dir}")
            os.makedirs(ssh_dir, mode=0o700)  # Diretório deve ter permissão 700

        if not os.path.exists(config_path):
            print(f"Criando arquivo {config_path}")
            with open(config_path, "w") as f:
                f.write("# Arquivo de configuração SSH\n")

            os.chmod(config_path, 0o600)  # Permissão 600 para segurança

    except PermissionError:
        print("Erro: Permissão negada ao criar ~/.ssh/config. Tente rodar o programa com sudo.")
        exit(1)

    return config_path
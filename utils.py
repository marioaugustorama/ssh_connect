import os

def verificar_ou_criar_ssh_config(config_path):
    """Verifica se o arquivo de configuração SSH existe e cria caso contrário."""
    ssh_dir = os.path.dirname(config_path)  # Obtém o diretório do arquivo config

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
        print(f"Erro: Permissão negada ao criar {config_path}. Tente rodar o programa com sudo.")
        exit(1)

    return config_path

def listar_chaves_locais(keys_dir):
    """Lista todas as chaves SSH privadas no diretório informado (ou ~/.ssh/ se não informado)."""
    if not keys_dir:
        keys_dir = os.path.expanduser("~/.ssh")

    chaves = []

    if not os.path.exists(keys_dir):
        return chaves  # Retorna lista vazia se o diretório não existir

    # Procura arquivos de chave privada (evita arquivos .pub)
    for arquivo in os.listdir(keys_dir):
        caminho_completo = os.path.join(keys_dir, arquivo)
        if os.path.isfile(caminho_completo) and not arquivo.endswith(".pub"):
            chaves.append(caminho_completo)

    return chaves


def obter_host_user(host, config_path=None):
    """Retorna o HostName e User do host a partir do arquivo ~/.ssh/config ou arquivo em outro local"""

    if config_path is None:
        config_path = os.path.expanduser("~/.ssh/config")

    hostname = None
    user = "root"  # Padrão caso não esteja definido
    capturando = False  

    if not os.path.exists(config_path):
        print(f"Erro: O arquivo de configuração '{config_path}' não existe.")
        return host, user
    
    
    with open(config_path, "r") as f:
        for linha in f:
            linha = linha.strip()

            # Detecta o bloco do host correto
            if linha.lower().startswith("host "):
                capturando = host in linha.split()[1:]
                continue

            if capturando:
                if linha.lower().startswith("hostname "):
                    hostname = linha.split()[1]
                elif linha.lower().startswith("user "):
                    user = linha.split()[1]

            if hostname and user:
                break  # Já temos os dados necessários

    return (hostname if hostname else host, user)  # Retorna os valores encontrados

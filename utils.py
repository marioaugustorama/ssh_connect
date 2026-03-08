from src.ssh_connect.services.config_service import ensure_ssh_config, get_host_user
from src.ssh_connect.services.key_service import list_local_private_keys


def verificar_ou_criar_ssh_config(config_path):
    """Compat wrapper para a nova service layer."""
    return ensure_ssh_config(config_path)


def listar_chaves_locais(keys_dir):
    """Compat wrapper para a nova service layer."""
    return list_local_private_keys(keys_dir)


def obter_host_user(host, config_path=None):
    """Compat wrapper para a nova service layer."""
    return get_host_user(host, config_path)

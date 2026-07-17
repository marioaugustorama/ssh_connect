from __future__ import annotations

import os
import subprocess

from src.ssh_connect.services.config_service import create_temp_config_with_keys


def copy_ssh_key(host: str, selected_key: str, config_path: str) -> None:
    """Copy a selected key to the target host using ssh-copy-id."""
    subprocess.run(["ssh-copy-id", "-F", config_path, "-i", selected_key, host], check=True)


def connect_ssh(host: str, config_path: str, keys_dir: str | None) -> None:
    """Connect to an SSH host, optionally using a temporary config with remapped keys."""
    temp_config_path = None
    final_config_path = config_path

    if keys_dir:
        temp_config_path = create_temp_config_with_keys(config_path, keys_dir)
        final_config_path = temp_config_path

    try:
        subprocess.run(["ssh", "-F", final_config_path, host])
    finally:
        if temp_config_path and os.path.exists(temp_config_path):
            os.remove(temp_config_path)

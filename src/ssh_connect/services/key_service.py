from __future__ import annotations

import os


def _looks_like_private_key(path: str) -> bool:
    """Return True when a file appears to be an SSH private key."""
    try:
        with open(path, "r", encoding="utf-8") as key_file:
            first_line = key_file.readline().strip()
    except (OSError, UnicodeDecodeError):
        return False

    if "PRIVATE KEY" in first_line:
        return True

    # Some OpenSSH keys are stored in PEM-like text without an explicit extension.
    return first_line == "-----BEGIN OPENSSH PRIVATE KEY-----"


def list_local_private_keys(keys_dir: str | None) -> list[str]:
    """List local private keys from the given directory."""
    if not keys_dir:
        keys_dir = os.path.expanduser("~/.ssh")

    if not os.path.exists(keys_dir):
        return []

    keys: list[str] = []

    for filename in os.listdir(keys_dir):
        full_path = os.path.join(keys_dir, filename)
        if os.path.isfile(full_path) and not filename.endswith(".pub") and _looks_like_private_key(full_path):
            keys.append(full_path)

    return keys

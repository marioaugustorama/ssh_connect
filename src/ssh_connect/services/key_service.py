from __future__ import annotations

import os


def list_local_private_keys(keys_dir: str | None) -> list[str]:
    """List local private keys from the given directory."""
    if not keys_dir:
        keys_dir = os.path.expanduser("~/.ssh")

    if not os.path.exists(keys_dir):
        return []

    keys: list[str] = []

    for filename in os.listdir(keys_dir):
        full_path = os.path.join(keys_dir, filename)
        if os.path.isfile(full_path) and not filename.endswith(".pub"):
            keys.append(full_path)

    return keys

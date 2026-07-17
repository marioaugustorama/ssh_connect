from __future__ import annotations

import getpass
import os
import tempfile
import unittest
from unittest.mock import patch

from src.ssh_connect.services.config_service import get_host_user, host_has_identity_file, parse_ssh_hosts
from src.ssh_connect.services.key_service import list_local_private_keys
from src.ssh_connect.services.ssh_service import copy_ssh_key


class ConfigServiceTests(unittest.TestCase):
    def test_parse_ssh_hosts_splits_multiple_aliases(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as config_file:
            config_file.write(
                "## production\n"
                "Host bastion jump\n"
                "  HostName 10.0.0.1\n"
                "  User alice\n"
            )
            config_path = config_file.name

        try:
            hosts, details = parse_ssh_hosts(config_path)

            self.assertEqual(hosts, ["bastion", "jump"])
            self.assertEqual(details["bastion"]["HostName"], "10.0.0.1")
            self.assertEqual(details["jump"]["User"], "alice")
            self.assertEqual(details["bastion"]["Comentário"], "production")
        finally:
            os.unlink(config_path)

    def test_get_host_user_defaults_to_current_user(self) -> None:
        current_user = getpass.getuser()

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as config_file:
            config_file.write(
                "Host prod\n"
                "  HostName 10.0.0.2\n"
            )
            config_path = config_file.name

        try:
            hostname, user = get_host_user("prod", config_path)
            self.assertEqual(hostname, "10.0.0.2")
            self.assertEqual(user, current_user)
        finally:
            os.unlink(config_path)

    def test_host_has_identity_file_uses_exact_host_match(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as config_file:
            config_file.write(
                "Host prod-db\n"
                "  IdentityFile ~/.ssh/id_rsa\n"
            )
            config_path = config_file.name

        try:
            self.assertFalse(host_has_identity_file("prod", config_path))
            self.assertTrue(host_has_identity_file("prod-db", config_path))
        finally:
            os.unlink(config_path)


class KeyServiceTests(unittest.TestCase):
    def test_list_local_private_keys_filters_non_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_key_path = os.path.join(temp_dir, "id_rsa")
            pub_key_path = os.path.join(temp_dir, "id_rsa.pub")
            config_path = os.path.join(temp_dir, "config")
            known_hosts_path = os.path.join(temp_dir, "known_hosts")

            with open(private_key_path, "w", encoding="utf-8") as private_key_file:
                private_key_file.write("-----BEGIN OPENSSH PRIVATE KEY-----\n")
                private_key_file.write("dummy\n")

            for path in (pub_key_path, config_path, known_hosts_path):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("not a key\n")

            keys = list_local_private_keys(temp_dir)
            self.assertEqual(keys, [private_key_path])


class SshServiceTests(unittest.TestCase):
    @patch("src.ssh_connect.services.ssh_service.subprocess.run")
    def test_copy_ssh_key_uses_config_file(self, mock_run) -> None:
        copy_ssh_key("prod", "/tmp/id_rsa", "/tmp/config")

        mock_run.assert_called_once_with(
            ["ssh-copy-id", "-F", "/tmp/config", "-i", "/tmp/id_rsa", "prod"],
            check=True,
        )


if __name__ == "__main__":
    unittest.main()

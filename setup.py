from __future__ import annotations

from setuptools import find_packages, setup


setup(
    name="ssh-connect",
    version="0.1.0",
    description="Gerenciador de conexões SSH com UI Textual e modo curses legado",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    license="MIT",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "textual>=8.0.2,<9",
    ],
    entry_points={
        "console_scripts": [
            "ssh-connect=ssh_connect.cli:main",
        ]
    },
)

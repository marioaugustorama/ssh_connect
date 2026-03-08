# SSH Connect - Gerenciador de Conexão SSH

Este script permite listar, selecionar e conectar-se a servidores SSH com base em um arquivo de configuração SSH personalizado. Ele também oferece suporte para modificar dinamicamente os caminhos das chaves SSH antes da conexão.

## 📌 Recursos

- ✅ Listagem interativa de hosts a partir do arquivo `~/.ssh/config` ou um arquivo personalizado.
- ✅ Suporte para um **arquivo de configuração alternativo** (`-f /caminho/para/config`).
- ✅ Opção para definir um **diretório de chaves SSH personalizado** (`-k /caminho/para/chaves`).
- ✅ **Modifica automaticamente os caminhos de `IdentityFile`**, se necessário.
- ✅ **Conexão direta** via linha de comando sem passar pelo menu interativo.
- ✅ **Interface curses** com barra de status e detalhes do host selecionado.
- ✅ Base inicial para futura migração para **Textual**.

---

## 🚀 Instalação e Dependências

### 🔹 **Requisitos**
- Python 3.x
- Módulos padrão: `curses`, `subprocess`, `tempfile`, `argparse`

### 🔹 **Clonar o repositório**
```sh
git clone https://github.com/marioaugustorama/ssh_connect.git
cd ssh_connect
chmod +x ssh-connect.py
```

🛠️ Uso

1️⃣ Modo Interativo (Usando ~/.ssh/config Padrão)
```sh
./ssh-connect.py

Isso irá listar os hosts do arquivo ~/.ssh/config e permitir a seleção interativa.
```

2️⃣ Usando um Arquivo de Configuração Personalizado
```sh
./ssh-connect.py -f /meu/arquivo/config

Isso carregará os hosts a partir de /meu/arquivo/config.
```

3️⃣ Definir um Diretório Alternativo para Chaves
```sh
./ssh-connect.py -f /meu/arquivo/config -k /minhas/chaves

Isso substituirá os caminhos de IdentityFile no config para /minhas/chaves/.
```

4️⃣ Conectar Diretamente a um Host Sem Menu
```sh
./ssh-connect.py -f /meu/arquivo/config -k /minhas/chaves meu-servidor

Isso conectará diretamente ao host meu-servidor, utilizando as configurações especificadas.
```

5️⃣ Ajuda e Opções Disponíveis
```sh
./ssh-connect.py --help

Exibe todas as opções disponíveis.
```

6️⃣ Iniciar o esqueleto da interface Textual
```sh
./ssh-connect.py --ui textual

Abre a base inicial da interface Textual. Requer a dependência `textual` instalada.
```

📌 Atalhos do Menu Interativo

| Tecla | Função |
|------ | ------ |
| ↑ / ↓ | Navegar entre os hosts |
| Enter | Conectar ao host selecionado | 
| PgUp/PgDn | Rolar a listagem |
| Home/End | Ir para o primeiro/ultimo host |
| Q / Esc | Sair do menu |


🚀 Exemplo de Uso (Modo Interativo)
```sh
./ssh-connect.py

📌 Saída esperada:

Selecione um host para conectar
--------------------------------------
> servidor-1
  servidor-2
  servidor-3
--------------------------------------
[↑/↓] Navegar  [Enter] Conectar  [Q/Esc] Sair
```

🛠️ Possíveis Melhorias Futuras

🌟 Suporte para favoritos, permitindo marcar hosts importantes.

🔍 Busca de hosts para encontrar rapidamente o servidor desejado.

📋 Exportação de logs das conexões.

## Estrutura inicial para integração

O projeto agora começa a separar a lógica em serviços para facilitar a integração futura com o `devops-tools`:

- `src/ssh_connect/services/config_service.py`
- `src/ssh_connect/services/key_service.py`
- `src/ssh_connect/services/ssh_service.py`
- `src/ssh_connect/tui/app.py`


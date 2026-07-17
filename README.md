# SSH Connect - Gerenciador de Conexão SSH

Este projeto lista hosts do `~/.ssh/config` ou de um arquivo alternativo, permite conexão direta e oferece uma interface Textual para navegação, seleção de chaves e logs.

## 📌 Recursos

- ✅ Listagem interativa de hosts a partir do arquivo `~/.ssh/config` ou um arquivo personalizado.
- ✅ Suporte para um **arquivo de configuração alternativo** (`-f /caminho/para/config`).
- ✅ Opção para definir um **diretório de chaves SSH personalizado** (`-k /caminho/para/chaves`).
- ✅ **Modifica automaticamente os caminhos de `IdentityFile`**, se necessário.
- ✅ **Conexão direta** via linha de comando sem passar pelo menu interativo.
- ✅ **Interface curses** como modo de compatibilidade com barra de status e detalhes do host selecionado.
- ✅ **Interface Textual** com abas para `Home`, `Hosts`, `Keys` e `Logs`.

---

## 🚀 Instalação e Dependências

### 🔹 **Requisitos**
- Python 3.x
- Módulos padrão: `curses`, `subprocess`, `tempfile`, `argparse`
- Dependência adicional para a TUI: `textual`

### 🔹 **Clonar o repositório**
```sh
git clone https://github.com/marioaugustorama/ssh_connect.git
cd ssh_connect
chmod +x ssh-connect.py
python3 -m pip install -r requirements.txt
```

## Uso

1️⃣ Modo Interativo padrão
```sh
./ssh-connect.py
```
Isso abre a interface Textual usando `~/.ssh/config`.

2️⃣ Usando um Arquivo de Configuração Personalizado
```sh
./ssh-connect.py -f /meu/arquivo/config
```
Isso carrega os hosts a partir de `/meu/arquivo/config`.

3️⃣ Definir um Diretório Alternativo para Chaves
```sh
./ssh-connect.py -f /meu/arquivo/config -k /minhas/chaves
```
Isso substitui os caminhos de `IdentityFile` para `/minhas/chaves/`.

4️⃣ Conectar Diretamente a um Host Sem Menu
```sh
./ssh-connect.py -f /meu/arquivo/config -k /minhas/chaves meu-servidor
```
Isso conecta diretamente ao host `meu-servidor` usando o config informado.

5️⃣ Ajuda e Opções Disponíveis
```sh
./ssh-connect.py --help
```
Exibe todas as opções disponíveis.

6️⃣ Iniciar a interface Textual explicitamente
```sh
./ssh-connect.py --ui textual
```
Abre a interface Textual com abas de `Home`, `Hosts`, `Keys` e `Logs`.

7️⃣ Usar a interface curses em terminais lentos
```sh
./ssh-connect.py --ui curses
```
Usa a interface legada baseada em `curses`. Se a interface Textual não estiver disponível, o programa também volta automaticamente para esse modo.

## Atalhos do Menu Interativo

| Tecla | Função |
|------ | ------ |
| ↑ / ↓ | Navegar entre os hosts |
| Enter | Conectar ao host selecionado |
| PgUp/PgDn | Rolar a listagem |
| Home/End | Ir para o primeiro/ultimo host |
| Q / Esc | Sair do menu |

## Exemplo de Uso

```text
./ssh-connect.py --ui curses

Saída esperada:

Selecione um host para conectar
--------------------------------------
> servidor-1
  servidor-2
  servidor-3
--------------------------------------
[↑/↓] Navegar  [Enter] Conectar  [Q/Esc] Sair
```

## Possíveis Melhorias Futuras

🌟 Suporte para favoritos, permitindo marcar hosts importantes.

🔍 Busca de hosts para encontrar rapidamente o servidor desejado.

📋 Exportação de logs das conexões.

## Estrutura da interface Textual

O projeto separa a lógica em serviços e a UI principal em telas Textual. O fluxo `curses` foi isolado em compatibilidade legada:

- `src/ssh_connect/services/config_service.py`
- `src/ssh_connect/services/key_service.py`
- `src/ssh_connect/services/ssh_service.py`
- `src/ssh_connect/tui/app.py`
- `src/ssh_connect/tui/screens/home.py`
- `src/ssh_connect/tui/screens/hosts.py`
- `src/ssh_connect/tui/screens/keys.py`
- `src/ssh_connect/tui/screens/logs.py`

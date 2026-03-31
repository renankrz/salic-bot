# Salic Bot

Bot para automação de prestação de contas no sistema [Salic](https://salic.cultura.gov.br). Usa [Playwright](https://playwright.dev/python/) para navegar pelo site, ler dados de um CSV de execução financeira e cadastrar comprovantes de despesa automaticamente, incluindo upload dos PDFs correspondentes.

Para detalhes sobre como organizar a pasta de clientes e o CSV de dados, veja [docs/DADOS.md](docs/DADOS.md).

## Uso

O bot possui duas interfaces: **GUI** e **CLI**.

### GUI

Execute sem argumentos para abrir a interface gráfica:

```bash
salic-bot
```

Preencha os campos (Mecanismo, Proponente, PRONAC, Pasta de Clientes, CPF e Senha) e clique em **RODAR**. As credenciais podem ser salvas no keyring do sistema operacional marcando "Lembrar credenciais". Para executar em modo dry run (preenche os campos mas cancela em vez de salvar), marque a caixa **Dry run**.

### CLI

Passe os argumentos pela linha de comando:

```bash
salic-bot \
  --mecanismo Mecenato \
  --proponente 11222333000181 \
  --pronac 241819 \
  --clientes-dir /caminho/para/clientes \
  --cpf 11122233344 \
  --senha SuaSenha
```

Para executar em modo **dry run** (preenche os campos mas cancela em vez de salvar cada comprovante):

```bash
salic-bot \
  --dry \
  --mecanismo Mecenato \
  --proponente 11222333000181 \
  --pronac 241819 \
  --clientes-dir /caminho/para/clientes \
  --cpf 11122233344 \
  --senha SuaSenha
```

Todos os argumentos são opcionais na linha de comando — se omitidos, o bot busca o valor em outras fontes (veja a seção de precedência abaixo). Porém, `proponente`, `pronac`, `clientes-dir`, `cpf` e `senha` são obrigatórios e precisam estar definidos em pelo menos uma fonte.

### Precedência de configuração

O bot resolve valores de configuração com a seguinte ordem de precedência (a primeira fonte com valor definido vence):

**CLI:**

| Campo | Precedência |
|---|---|
| mecanismo, proponente, pronac, clientes_dir | argumento CLI → `.env` → QSettings → default |
| cpf, senha | argumento CLI → `.env` → keyring → default |

**GUI (pré-preenchimento dos campos):**

| Campo | Precedência |
|---|---|
| mecanismo, proponente, pronac, clientes_dir | `.env` → QSettings → default |
| cpf, senha | `.env` → keyring → default |

> As variáveis definidas no `.env` têm precedência sobre todas as outras fontes de configuração persistentes (QSettings, keyring).

### Variáveis de ambiente

Copie o arquivo de exemplo e preencha:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `MECANISMO` | Mecanismo do projeto (ex: `Mecenato`) |
| `PROPONENTE` | CNPJ do proponente (somente dígitos) |
| `PRONAC` | Número do PRONAC |
| `CLIENTES_DIR` | Caminho absoluto para a pasta raiz de clientes |
| `USER_CPF` | CPF do usuário (somente dígitos) |
| `USER_SENHA` | Senha do usuário |
| `HEADLESS` | Executar sem interface do navegador (`True`/`False`, padrão: `False`) |
| `SLOW_MO` | Delay entre ações do Playwright em ms (padrão: `100`) |
| `PLAYWRIGHT_BROWSERS_PATH` | Caminho para os browsers do Playwright (padrão: `./browsers`) |

## Desenvolvimento

O projeto usa [uv](https://docs.astral.sh/uv/) para gerenciamento de dependências e ambiente virtual.

### Setup

```bash
# Instalar dependências e criar o ambiente virtual
uv sync --dev

# Instalar o Chromium do Playwright
PLAYWRIGHT_BROWSERS_PATH=./browsers uv run python -m playwright install chromium

# Copiar e preencher o .env
cp .env.example .env
```

### Executar em modo desenvolvimento

```bash
# GUI
uv run salic-bot

# CLI
uv run salic-bot --proponente 11222333000181 --pronac 241819 --clientes-dir /caminho/para/clientes --cpf 11122233344 --senha SuaSenha
```

### Build

O executável é gerado com [PyInstaller](https://pyinstaller.org/) e embute o Chromium. O script `build.sh` automatiza o processo:

```bash
./build.sh
```

O executável é gerado em `dist/salic-bot`.

### CI/CD

O repositório inclui um workflow GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml)) que gera builds para Linux, macOS e Windows quando uma tag de versão é criada (ex: `v0.1.0`). Os executáveis são publicados automaticamente como assets de um GitHub Release.

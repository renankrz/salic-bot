# Salic Bot

Bot para automação de prestação de contas no sistema Salic.

## Desenvolvimento

### 1. Criar e ativar um ambiente virtual

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Instalar o pacote em modo desenvolvimento

Este projeto utiliza o layout `src/`, portanto o pacote precisa ser instalado
em modo *editable* para que os imports funcionem corretamente durante o
desenvolvimento.

```bash
pip install -e .
```

### 4. Instalar o browser do Playwright

```bash
playwright install chromium
```

### 5. Configurar o ambiente

```bash
cp .env.example .env
```

e preencha as variáveis necessárias.

### 6. Executar o bot

```bash
python3 -m salic_bot
```

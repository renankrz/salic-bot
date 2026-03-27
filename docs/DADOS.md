# Organização dos Dados

Este documento descreve como o bot espera encontrar a pasta de clientes e os arquivos necessários para a automação.

## Estrutura de pastas

A pasta raiz de clientes (configurada via `CLIENTES_DIR`, `--clientes-dir` ou pela GUI) deve seguir esta hierarquia:

```
clientes/
└── <Nome do Cliente> - <CNPJ>/
    └── <Nome do Projeto> - <PRONAC>/
        └── 04. Execução Financeira/
            ├── <nome>.csv
            └── NFs, Recibos, Fatura + boletos/
                ├── 2025.01/
                │   ├── 2025.01.09_NF_35_Oficineira_Maria.pdf
                │   ├── 2025.01.20_NF_19_Coordenador técnico_Joana.pdf
                │   └── ...
                ├── 2025.02/
                │   ├── 2025.02.25_NF_123_Cenografia_Mario.pdf
                │   └── ...
                └── ...
```

### Regras de localização

O bot navega pela estrutura usando correspondências parciais:

1. **Pasta do cliente** — procura dentro de `clientes/` uma pasta cujo nome contenha o **CNPJ** (somente dígitos) do proponente.
2. **Pasta do projeto** — dentro da pasta do cliente, procura uma pasta cujo nome contenha o **PRONAC**.
3. **Pasta de execução financeira** — dentro da pasta do projeto, procura uma pasta cujo nome comece com `04`.
4. **CSV de dados** — o primeiro arquivo `.csv` encontrado dentro da pasta de execução financeira.
5. **Pasta de comprovantes (PDFs)** — dentro da pasta de execução financeira, procura uma pasta cujo nome contenha `nfs` (case-insensitive).

## CSV de execução financeira

O CSV deve estar codificado em **UTF-8** (com ou sem BOM) e conter as seguintes colunas:

| Coluna | Descrição | Exemplo |
|---|---|---|
| Produto | Produto da rubrica | `Curso / Oficina / Capacitação` |
| Etapa | Etapa da rubrica | `Pré-Produção / Preparação` |
| UF | Unidade federativa | `SP` |
| Cidade | Cidade | `São Paulo` |
| Item de Custo | Item de custo da rubrica | `Agente educativo(a): Oficineiro(a)` |
| CPF | CPF do fornecedor (vazio se CNPJ preenchido) | `123.456.789-00` |
| CNPJ | CNPJ do fornecedor (vazio se CPF preenchido) | `27.801.445/0001-27` |
| Tipo Comprovante | Tipo do comprovante de despesa | `Nota Fiscal/Fatura` |
| Data de Emissão | Data de emissão do comprovante (`D/M/YYYY`) | `9/1/2025` |
| Número | Número do comprovante | `35` |
| Série | Série do comprovante (pode ser vazio) | |
| Forma de Pagamento | Forma de pagamento | `Transferência Bancária` |
| Data do pagamento | Data em que o pagamento foi efetuado (`D/M/YYYY`) | `10/1/2025` |
| Nº Documento Pagamento | Número do documento de pagamento | `11005` |
| Valor | Valor pago (formato brasileiro) | `R$ 2.200,00` |
| Justificativa | Justificativa (obrigatória quando o valor ultrapassa o permitido) | |

## Nomenclatura dos PDFs de comprovante

O bot localiza o PDF correspondente a cada linha do CSV usando a **Data de Emissão** e o **Número** do comprovante. O nome do arquivo deve seguir o padrão:

```
<YYYY.mm.DD>_<tipo>_<número>_<descrição>.pdf
```

Onde:

- `<YYYY.mm.DD>` — data de emissão formatada (ex: `2025.01.09` para `9/1/2025`)
- `<número>` — o número do comprovante, precedido por `_` e seguido por `_`
- O restante do nome é livre

O bot procura em **todas as subpastas** dentro da pasta de comprovantes (organizadas por mês, ex: `2025.01/`, `2025.02/`) por um arquivo cujo nome comece com `<YYYY.mm.DD>_` e contenha `_<número>_`.

### Exemplos

Para uma linha do CSV com Data de Emissão `9/1/2025` e Número `35`:

```
✓  2025.01.09_NF_35_Oficineira_Maria.pdf
✗  2025.01.09_NF_Oficineira.pdf          (sem o número)
✗  2025.02.09_NF_35_Oficineira.pdf       (data diferente)
```

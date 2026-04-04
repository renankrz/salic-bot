# Organização dos Dados

Este documento descreve como o bot espera encontrar os arquivos necessários para a automação: o CSV com itens de custo e os PDFs de comprovantes.

## CSV com itens de custo

O caminho do CSV é fornecido diretamente pelo usuário (via GUI, CLI ou variável de ambiente `ITENS_CSV`).

O CSV deve estar codificado em **UTF-8** (com ou sem BOM) e conter as seguintes colunas:

| Coluna | Descrição | Exemplo |
|---|---|---|
| Produto | Produto da rubrica | `Curso / Oficina / Capacitação` |
| Etapa | Etapa da rubrica | `Pré-Produção / Preparação` |
| UF | Unidade federativa da rubrica | `SP` |
| Cidade | Cidade da rubrica | `São Paulo` |
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

**Observação:** Os nomes das colunas não diferenciam maiúsculas de minúsculas (case-insensitive).

> Por exemplo, `Produto`, `produto` ou `PRODUTO` serão reconhecidos da mesma forma.

## Pasta de comprovantes (PDFs)

O caminho da pasta de comprovantes é fornecido diretamente pelo usuário (via GUI, CLI ou variável de ambiente `COMPROVANTES_DIR`).

O bot busca recursivamente em **todas as subpastas** dentro da pasta de comprovantes por arquivos correspondentes a cada linha do CSV.

Exemplo de estrutura da pasta de comprovantes:

```
comprovantes/
├── 2025.01/
│   ├── 2025.01.09_NF_35_Oficineira_Maria.pdf
│   ├── 2025.01.20_NF_19_Coordenador técnico_Joana.pdf
│   └── ...
├── 2025.02/
│   ├── 2025.02.25_NF_123_Cenografia_Mario.pdf
│   └── ...
└── ...
```

A organização interna (por mês, por tipo, etc.) é livre — o bot procura recursivamente.

### Nomenclatura dos PDFs de comprovante

O bot localiza o PDF correspondente a cada linha do CSV usando a **Data de Emissão** e o **Número** do comprovante. O nome do arquivo deve seguir o padrão:

```
<YYYY.mm.DD>_<tipo>_<número>_<descrição>.pdf
```

Onde:

- `<YYYY.mm.DD>` — data de emissão formatada (ex: `2025.01.09` para `9/1/2025`)
- `<número>` — o número do comprovante, precedido por `_` e seguido por `_`
- O restante do nome é livre

### Exemplos

Para uma linha do CSV com Data de Emissão `9/1/2025` e Número `35`:

```
✓  2025.01.09_NF_35_Oficineira_Maria.pdf
✗  2025.01.09_NF_Oficineira.pdf          (incorreto, sem o número)
✗  2025.02.09_NF_35_Oficineira.pdf       (incorreto, data diferente)
```

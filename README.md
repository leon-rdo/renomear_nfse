# Renomeador de NFS-e

Utilitário de linha de comando que renomeia os arquivos **XML e PDF** de Notas Fiscais de Serviço Eletrônicas (NFS-e) baixados do portal [nfse.gov.br](https://www.nfse.gov.br) para nomes legíveis e padronizados.

## Problema que resolve

O portal nfse.gov.br gera arquivos com nomes gerados automaticamente (ex: `150140222XXXXXXXXXXXX39000000000003225116XXXXXX591.xml`). Este script os renomeia para um formato legível por humanos:

```
NF20 - 2025-01-28 - Empresa Tomadora - R$ 1.500,00.xml
NF25 - 2025-06-23 - Empresa Tomadora - R$ 1.656,00 [CANCELADA].xml
```

## Requisitos

- Python 3.8 ou superior
- Sem dependências externas — usa apenas a biblioteca padrão do Python

## Instalação

```bash
git clone https://github.com/leon-rdo/renomear_nfse.git
cd renomear_nfse
```

## Uso

O script pode ser executado de duas formas: **modo interativo** (sem argumentos) ou **modo direto** (passando os caminhos pela linha de comando).

### Modo interativo

Basta rodar o script sem argumentos e ele perguntará os caminhos:

```bash
python3 renomear_nfse.py
```

```
Nenhuma pasta informada via argumento. Modo interativo.

Caminho da pasta com os XMLs: ~/Downloads/NFs/XML
Caminho da pasta com os PDFs: ~/Downloads/NFs/PDF
```

### Modo direto (linha de comando)

```bash
python3 renomear_nfse.py --xml-dir <pasta_dos_xmls> [opções]
```

### Argumentos

| Argumento | Obrigatório | Descrição |
|---|---|---|
| `--xml-dir DIR` | Não | Pasta com os arquivos `.xml`. Se omitido, é solicitado interativamente |
| `--pdf-dir DIR` | Não | Pasta com os arquivos `.pdf`. Se omitido, é solicitado interativamente (ou usa a pasta irmã `PDF/`) |
| `--canceladas N,N,...` | Não | Números das notas canceladas, separados por vírgula |
| `--dry-run` / `-n` | Não | Simula as renomeações sem alterar nenhum arquivo |

### Exemplos

```bash
# Modo interativo — o script pergunta as pastas
python3 renomear_nfse.py

# Pastas informadas diretamente
python3 renomear_nfse.py --xml-dir ./XML --pdf-dir ./PDF

# Simular antes de executar (recomendado na primeira vez)
python3 renomear_nfse.py --xml-dir ~/Downloads/NFs/XML --pdf-dir ~/Downloads/NFs/PDF --dry-run

# Marcar notas 25 e 32 como canceladas
python3 renomear_nfse.py --xml-dir ./XML --pdf-dir ./PDF --canceladas 25,32
```

### Fluxo recomendado

1. Rode com `--dry-run` para conferir o resultado antes de alterar qualquer arquivo.
2. Se estiver correto, rode novamente sem `--dry-run`.

```bash
# 1. Simular
python3 renomear_nfse.py --dry-run

# 2. Aplicar
python3 renomear_nfse.py
```

## Formato de saída

O nome gerado segue o padrão:

```
NF<número> - <data> - <tomador> - <valor>[.xml|.pdf]
```

- **Número**: zero-à-esquerda quando abaixo de 10 (ex: `NF07`)
- **Data**: formato `AAAA-MM-DD` (ISO 8601), extraída do campo `dhProc` do XML
- **Tomador**: nome do contratante com sufixos jurídicos removidos (`LTDA`, `S.A.`, `EIRELI`, etc.) e Title Case aplicado com regras do português
- **Valor**: formato brasileiro (`R$ 1.500,00`)
- **`[CANCELADA]`**: adicionado ao final quando o número da nota está em `--canceladas`

## Estrutura esperada dos arquivos

O script espera a estrutura de pastas gerada pelo portal nfse.gov.br, onde o PDF de cada nota tem o mesmo nome base do XML:

```
Downloads/
└── NFs/
    ├── XML/
    │   ├── 150140222XXXXXXXXXXXX39000000000003225116XXXXXX591.xml
    │   └── 230140222XXXXXXXXXXXX39000000000003225116XXXXXX592.xml
    └── PDF/
        ├── 150140222XXXXXXXXXXXX39000000000003225116XXXXXX591.pdf
        └── 230140222XXXXXXXXXXXX39000000000003225116XXXXXX592.pdf
```

## Compatibilidade

Compatível com o padrão **NFS-e Nacional** (namespace `http://www.sped.fazenda.gov.br/nfse`), implementado pelo portal nfse.gov.br a partir de 2023. Notas emitidas em sistemas municipais legados podem usar um schema diferente e não são suportadas.

## Licença

MIT

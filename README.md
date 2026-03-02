# Tratamento FCK (.ttx → Excel) — Streamlit

App em **Streamlit** para **enviar arquivos `.ttx`**, **extrair e tratar** os dados de resistência do concreto (FCK) e **baixar um Excel** consolidado.  
O app também exibe uma **prévia (início da planilha)** na tela.

## Funcionalidades
- Upload de arquivo **`.ttx`**
- Extração e consolidação dos registros em uma tabela
- Tratamentos principais:
  - Conversão de números com vírgula para float (ex.: `60,5` → `60.5`)
  - Coluna **MÊS** convertida e formatada como `MM/YYYY` no Excel
  - Valores `28_DIAS = 0` tratados como vazio (`NaN`)
- Prévia dos primeiros registros no app
- Download do **Excel tratado** (`.xlsx`)

## Estrutura do projeto

streamlit/
├─ app.py
├─ requirements.txt
├─ .gitignore
└─ README.md

## Requisitos
- Python 3.10+ (recomendado 3.12)

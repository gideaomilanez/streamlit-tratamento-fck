import io
import re
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st


def numero(valor_string):
    try:
        return float(str(valor_string).replace(",", "."))
    except (ValueError, TypeError):
        return None


def formatar_mes(texto_periodo):
    if not texto_periodo:
        return None
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(texto_periodo))
    if match:
        mes = int(match.group(2))
        ano = int(match.group(3))
        return datetime(ano, mes, 1)
    return None


def extrair_dados_ttx_bytes(conteudo_bytes: bytes):

    texto = conteudo_bytes.decode("latin-1", errors="replace")
    dados_extraidos = []

    mes_raw = ""
    cliente = ""
    obra = ""
    usina = ""
    peca = ""
    dt_mold = ""

    for linha in texto.splitlines():

        linha = linha.strip()

        if not linha:
            continue

        partes = [p.strip('" ') for p in linha.split("\t")]

        if not partes:
            continue

        if linha.startswith('"Periodo Moldagem:'):
            match = re.search(r"Periodo Moldagem:\s*(.*)", partes[0])
            if match:
                mes_raw = match.group(1)

        elif linha.startswith('"Cliente:'):
            match = re.search(r"Cliente:\s*(.*)", partes[0])
            if match:
                cliente = match.group(1)

        elif linha.startswith('"Contrato:'):
            for i, p in enumerate(partes):
                if p == "Obra:" and i + 1 < len(partes):
                    obra = partes[i + 1]

        elif linha.startswith('"Usina:'):
            match = re.search(r"Usina:\s*(.*)", partes[0])
            if match:
                usina = match.group(1)

            for p in partes:
                if p.startswith("Peca Concretar:"):
                    peca = p.replace("Peca Concretar:", "").strip()

        elif linha.startswith('"Dt.Mold.:'):
            match = re.search(r"Dt\.Mold\.:\s*(.*)", partes[0])
            if match:
                dt_mold = match.group(1)

        elif partes[0].isdigit():

            if len(partes) >= 15:

                nf = partes[0]
                bt = partes[2]
                uso = partes[3]
                brita = partes[4]
                slump = numero(partes[5])
                cimento = partes[7]
                fck = numero(partes[8])
                maior_7 = numero(partes[11])
                _28dias_1 = numero(partes[12])
                _28dias_2 = numero(partes[13])
                maior_28 = numero(partes[14])

                # Tratar 0.0 como NaN
                if maior_28 == 0.0:
                    maior_28 = np.nan
                if _28dias_1 == 0.0:
                    _28dias_1 = np.nan
                if _28dias_2 == 0.0:
                    _28dias_2 = np.nan

                dados_extraidos.append(
                    {
                        "USINA": usina,
                        "MÊS": formatar_mes(mes_raw),
                        "DATA MOLDAGEM": dt_mold,
                        "NF": nf,
                        "BT": bt,
                        "CLIENTE": cliente,
                        "OBRA": obra,
                        "USO": uso,
                        "FCK": fck,
                        "SLUMP": slump,
                        "BRITA": brita,
                        "PEÇA": peca,
                        "TIPO DE CIMENTO": cimento,
                        "7_DIAS": maior_7,
                        "28_DIAS_1": _28dias_1,
                        "28_DIAS_2": _28dias_2,
                        "28_DIAS": maior_28,
                    }
                )

    return dados_extraidos


def df_para_excel_bytes(df: pd.DataFrame) -> bytes:

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl", date_format="MM/YYYY") as writer:

        df.to_excel(writer, index=False, sheet_name="Dados")

        ws = writer.sheets["Dados"]

        colunas = list(df.columns)

        if "MÊS" in colunas:

            col_idx = colunas.index("MÊS") + 1

            for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
                for cell in row:
                    cell.number_format = "MM/YYYY"

    buffer.seek(0)

    return buffer.getvalue()


def nome_arquivo_saida(df: pd.DataFrame) -> str:

    meses_validos = df["MÊS"].dropna() if "MÊS" in df.columns else pd.Series([], dtype="datetime64[ns]")

    mes_ref = meses_validos.iloc[0] if len(meses_validos) else datetime.now()

    return mes_ref.strftime("%Y-%m") + "-database.xlsx"


st.set_page_config(page_title="Tratamento FCK (.ttx → Excel)", layout="wide")

st.title("Tratamento FCK (.ttx → Excel)")

st.write(
    "Envie um arquivo **.ttx**. O app vai tratar e gerar um **Excel** para download."
)

arquivo = st.file_uploader("Upload do arquivo .ttx", type=["ttx"])


if arquivo is not None:

    with st.spinner("Lendo e tratando o arquivo..."):

        conteudo = arquivo.read()

        dados = extrair_dados_ttx_bytes(conteudo)

        if not dados:
            st.error("Não consegui extrair registros desse .ttx.")
            st.stop()

        df = pd.DataFrame(dados)

    c1, c2, c3 = st.columns(3)

    c1.metric("Arquivo", arquivo.name)
    c2.metric("Registros extraídos", f"{len(df):,}".replace(",", "."))
    c3.metric("Colunas", str(df.shape[1]))

    st.subheader("Prévia da planilha")

    st.dataframe(df.head(20), use_container_width=True)

    excel_bytes = df_para_excel_bytes(df)

    saida = nome_arquivo_saida(df)

    st.download_button(
        label="⬇️ Baixar Excel tratado",
        data=excel_bytes,
        file_name=saida,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

import pandas as pd
import streamlit as st

def read_from_gsheets(hub_key: str) -> pd.DataFrame:
    import gspread
    from gspread_dataframe import get_as_dataframe
    from google.oauth2.service_account import Credentials

    sheet_id = st.secrets.get("sheets", {}).get(hub_key)
    tab = st.secrets.get("tabs", {}).get(hub_key, "DATA")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(tab)

    raw_df = get_as_dataframe(ws, evaluate_formulas=True, header=None)
    raw_df = raw_df.dropna(how="all")   # quitar filas vacías

    # Tomar la primera fila no vacía como encabezados
    new_header = raw_df.iloc[0]
    df = raw_df[1:].copy()
    df.columns = [str(c).strip().upper() for c in new_header]

    return df

@st.cache_data(ttl=300, show_spinner=False)
def load_data(hub_label: str) -> pd.DataFrame:
    key = hub_label.lower().replace(" ", "")
    return read_from_gsheets(key)
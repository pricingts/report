import streamlit as st
from src.data_loader import load_data
from src.helpers.utils import STATUS_MAP, DEFAULT_COLS, OPTIONAL_COLS, preprocess_df

def sidebar_filters():
    st.sidebar.header("Filtros")
    hub = st.sidebar.selectbox("Seleccionar HUB", ["EXPO 1", "EXPO 2", "IMPO"])
    language = st.sidebar.radio("Idioma de Status", ["es", "en"], format_func=lambda x: "Español" if x=="es" else "English")

    df = load_data(hub)

    df_all = preprocess_df(df, hub)

    # 🔹 Obtener clientes únicos combinando SHIPPER y CONSIGNEE
    shipper_vals = df_all["SHIPPER"].dropna().astype(str).unique() if "SHIPPER" in df_all.columns else []
    consignee_vals = df_all["CONSIGNEE"].dropna().astype(str).unique() if "CONSIGNEE" in df_all.columns else []
    clients = sorted(set(list(shipper_vals) + list(consignee_vals)))

    client = st.sidebar.multiselect("Seleccionar cliente(s)", options=clients)

    estado_options = list(STATUS_MAP.keys())
    estado_labels = {k: f"{k} - {STATUS_MAP[k][language]}" for k in estado_options}
    estados_seleccionados = st.sidebar.multiselect(
    "Seleccionar estado(s)", options=estado_options, format_func=lambda k: estado_labels[k]
    )

    all_cols = [c for c in (DEFAULT_COLS + OPTIONAL_COLS) if c in df_all.columns]
    selected_cols = st.sidebar.multiselect(
    "Escoger columnas", options=all_cols, default=[c for c in DEFAULT_COLS if c in all_cols]
    )

    return hub, language, client, estados_seleccionados, selected_cols, df_all
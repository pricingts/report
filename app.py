import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
from src.helpers.auth import check_authentication

from src.data_loader import load_data
from src.filters import sidebar_filters
from src.helpers.utils import translate_status

st.set_page_config(page_title="Reporte de Estado de Cargas", layout="wide")
st.header("📦 Reporte de Estado de Cargas")

check_authentication()

# Sidebar: filtros y carga de datos
hub, language, client, estados_seleccionados, selected_cols, df_all = sidebar_filters()

# Aplicar filtros
filtered = df_all.copy()
if client: # lista de clientes seleccionados
    filtered = filtered[
        (filtered["SHIPPER"].astype(str).isin(client)) |
        (filtered["CONSIGNEE"].astype(str).isin(client))
        ]
if estados_seleccionados:
    from src.helpers.utils import detect_status_code
    status_codes = filtered["STATUS"].apply(detect_status_code)
    filtered = filtered[status_codes.isin(estados_seleccionados)]

# Traducir status
show_df = filtered.copy()
show_df["STATUS"] = show_df["STATUS"].apply(lambda v: translate_status(v, language))

# Columna de comentarios
if "COMENTARIOS" not in show_df.columns:
    show_df["COMENTARIOS"] = ""

cols_to_show = [c for c in selected_cols if c in show_df.columns] + ["COMENTARIOS"]

st.subheader("Resultados")
st.caption("*Puedes editar la columna **COMENTARIOS** antes de generar el PDF.*")

client_name = st.text_input('Nombre del Cliente', key='nombre')

edited = st.data_editor(
    show_df[cols_to_show],
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="editable_table"
)

st.divider()
col1, col2 = st.columns([1, 1])

with col1:
    st.write(f"Filas: **{edited.shape[0]}** | Columnas: **{edited.shape[1]}**")

with col2:
    filename = f"reporte_cargas.pdf"

    if st.button("🖨️ Generar PDF", type="primary", use_container_width=True):
        # Copia del dataframe final
        df_pdf = edited.copy()
        df_pdf["STATUS"] = df_pdf["STATUS"].apply(lambda v: translate_status(v, language))

        if "COMENTARIOS" in df_pdf.columns:
            # Si está totalmente vacía → eliminar
            if df_pdf["COMENTARIOS"].astype(str).str.strip().replace("None", "").eq("").all():
                df_pdf = df_pdf.drop(columns=["COMENTARIOS"])
            else:
                # Si tiene valores → enviarla al final
                cols = [c for c in df_pdf.columns if c != "COMENTARIOS"] + ["COMENTARIOS"]
                df_pdf = df_pdf[cols]

        # 🔹 Crear overlay
        from src.pdf_writer import build_overlay, merge_with_template

        overlay_bytes = overlay_bytes = build_overlay(
                df_pdf,
                client_name,
                language,
                "resources/templates/reporte.pdf"   # 👈 se pasa aquí también
            )

        # 🔹 Superponer sobre plantilla
        output_buffer = io.BytesIO()
        merge_with_template(
            "resources/templates/reporte.pdf",
            overlay_bytes,
            output_buffer
        )

        os.makedirs("output", exist_ok=True)

        pdf_bytes = output_buffer.getvalue()

        # ruta final en carpeta output
        output_path = os.path.join("resources/output", filename)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        # botón para descargar en streamlit
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )

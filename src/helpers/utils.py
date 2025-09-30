import pandas as pd

STATUS_MAP = {
    "R": {"es": "GESTIÓN DE RESERVA", "en": "RESERVE MANAGEMENT"},
    "C": {"es": "EMBARQUE EN DOCUMENTACIÓN", "en": "SHIPPING DOCUMENTATION"},
    "Z": {"es": "EN ESPERA DE SALIDA", "en": "WAITING FOR DEPARTURE"},
    "S": {"es": "ENVIAR INSTRUCCIONES DE SWITCH", "en": "SEND SWITCH INSTRUCTIONS"},
    "T": {"es": "CARGA EN TRANSITO", "en": "CARGO IN TRANSIT"},
    "L": {"es": "CARGA EN TRANSITO Y SIN ORDEN DE LIBERACIÓN", "en": "CARGO IN TRANSIT AND WITHOUT RELEASE ORDER"},
    "P": {"es": "CARGA EN DESTINO | CONTENEDOR NO RETIRADO", "en": "LOAD AT DESTINATION | CONTAINER NOT PICKED UP"},
    "D": {"es": "CONTENEDOR VACIO NO RETORNADO", "en": "EMPTY CONTAINER NOT RETURNED"},
}

DEFAULT_COLS = [
    "CASE ID", "CLIENT REF", "BILL", "VOL", "SHIPPER", "CONSIGNEE",
    "ORIGIN", "DESTINATION", "ETD", "ETA", "STATUS"
]
OPTIONAL_COLS = ["EMPTY PICK UP", "FINAL DESTINATION", "SHIPPING LINE", "CONTAINERS #"]

COLUMN_RENAMES = {
    "CASE": "CASE ID",
    "REF. CLIENTE": "CLIENT REF",
    "SHIPPING_LINE": "SHIPPING LINE",
    "CONTAINER NUM": "CONTAINERS #"
}


def detect_status_code(value: str) -> str:
    if not value:
        return ""
    v = str(value).strip()
    if v in STATUS_MAP:
        return v
    for code, labels in STATUS_MAP.items():
        if v.upper() in (labels["es"].upper(), labels["en"].upper()):
            return code
    return ""

def translate_status(value: str, lang: str) -> str:
    code = detect_status_code(value)
    if code in STATUS_MAP:
        return STATUS_MAP[code][lang]
    return str(value)

def preprocess_df(df: pd.DataFrame, hub: str) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.rename(columns={col: COLUMN_RENAMES[col] for col in df.columns if col in COLUMN_RENAMES})
    if "VOL" in df.columns and "UNIT" in df.columns:
        df["VOL"] = df["VOL"].astype(str).str.strip() + "x" + df["UNIT"].astype(str).str.strip()

    if hub.lower().startswith("impo"):  # Importaciones
        if "HBL/HAWB" in df.columns:
            df["BILL"] = df["HBL/HAWB"].astype(str).str.strip()

    elif hub.lower().startswith("expo 1"): 
        if "BOOKING" in df.columns and "BL_HBL" in df.columns:
            df["BILL"] = df["BL_HBL"].astype(str).str.strip() + "/ " + df["BOOKING"].astype(str).str.strip()

    else:
        if "MBL_MAWB HBL_HAWB" in df.columns and "MBL_MAWB HBL_HAWB" in df.columns:
            df["BILL"] = df["MBL_MAWB HBL_HAWB"].astype(str).str.strip() + "/ " + df["BOOKING"].astype(str).str.strip()

    return df

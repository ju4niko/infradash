from fastapi import FastAPI
from pathlib import Path
import pandas as pd
import re
import unicodedata

app = FastAPI()


def normalize_column(name: str) -> str:
    """
    Normaliza nombres de columnas:
    - trim espacios
    - lowercase
    - elimina acentos
    - espacios -> _
    - elimina caracteres especiales
    """

    # convierte a string por seguridad
    name = str(name)

    # trim + lowercase
    name = name.strip().lower()

    # elimina acentos
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # reemplaza espacios múltiples por _
    name = re.sub(r"\s+", "_", name)

    # elimina caracteres especiales
    name = re.sub(r"[^a-z0-9_]", "", name)

    # elimina múltiples _
    name = re.sub(r"_+", "_", name)

    # elimina _ al inicio/final
    name = name.strip("_")

    return name


@app.get("/")
def root():
    return {"status": "infradash backend ok"}


@app.get("/api/import")
def import_excel():

    uploads = Path("/app/data/uploads")

    files = list(uploads.glob("*.xlsx"))

    result = []

    for file in files:

        try:

            # fuerza engine openpyxl
            df = pd.read_excel(file, engine="openpyxl")

            # normaliza nombres de columnas
            df.columns = [normalize_column(col) for col in df.columns]

            # limpia strings del dataframe
            df = df.map(
                lambda x: x.strip() if isinstance(x, str) else x
            )

            # convierte qty_nes a numerico
            if "qty_nes" in df.columns:

                df["qty_nes_numeric"] = pd.to_numeric(
                    df["qty_nes"],
                    errors="coerce"
                ).fillna(0)

            else:

                df["qty_nes_numeric"] = 0

            # summary
            total_nes = int(df["qty_nes_numeric"].sum())

            vendors = []
            if "vendor" in df.columns:
                vendors = sorted(
                    df["vendor"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

            technologies = []
            if "tecnologia" in df.columns:
                technologies = sorted(
                    df["tecnologia"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

            # convierte NaN a ""
            clean_df = df.fillna("")

            result.append({
                "file": file.name,

                "rows": len(clean_df),

                "columns": list(clean_df.columns),

                "summary": {
                    "total_systems": len(clean_df),
                    "total_nes": total_nes,
                    "vendors": vendors,
                    "technologies": technologies
                },

                "data": clean_df.to_dict(orient="records")
            })

        except Exception as e:

            result.append({
                "file": file.name,
                "error": str(e)
            })

    return result

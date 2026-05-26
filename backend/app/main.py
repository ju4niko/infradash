from fastapi import FastAPI
from pathlib import Path
import pandas as pd
import re

app = FastAPI()


def normalize_column(name: str) -> str:
    """
    Normaliza nombres de columnas:
    - trim espacios
    - lowercase
    - espacios -> _
    - elimina caracteres especiales
    """

    name = name.strip().lower()

    # reemplaza espacios múltiples por _
    name = re.sub(r"\s+", "_", name)

    # elimina caracteres especiales
    name = re.sub(r"[^a-z0-9_]", "", name)

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

            df = pd.read_excel(file)

            # normaliza columnas
            df.columns = [normalize_column(col) for col in df.columns]

            result.append({
                "file": file.name,
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.fillna("").to_dict(orient="records")
            })

        except Exception as e:

            result.append({
                "file": file.name,
                "error": str(e)
            })

    return result

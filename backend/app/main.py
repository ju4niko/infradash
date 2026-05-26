from fastapi import FastAPI
from pathlib import Path
import pandas as pd

app = FastAPI()

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

            result.append({
                "file": file.name,
                "rows": len(df),
                "columns": list(df.columns)
            })

        except Exception as e:

            result.append({
                "file": file.name,
                "error": str(e)
            })

    return result

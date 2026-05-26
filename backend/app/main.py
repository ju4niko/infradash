from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

import pandas as pd
import re
import unicodedata

from .database import SessionLocal
from .database import engine
from .database import Base

from .models import System
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

# crea tablas automáticamente
Base.metadata.create_all(bind=engine)


def normalize_column(name: str) -> str:

    name = str(name)

    name = name.strip().lower()

    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    name = re.sub(r"\s+", "_", name)

    name = re.sub(r"[^a-z0-9_]", "", name)

    name = re.sub(r"_+", "_", name)

    name = name.strip("_")

    return name


@app.get("/")
def root():

    return {
        "status": "infradash backend ok"
    }


@app.get("/api/import")
def import_excel():

    uploads = Path("/app/data/uploads")

    files = list(uploads.glob("*.xlsx"))

    result = []

    db = SessionLocal()

    for file in files:

        try:

            df = pd.read_excel(
                file,
                engine="openpyxl"
            )

            # normaliza columnas
            df.columns = [
                normalize_column(col)
                for col in df.columns
            ]

            # limpia strings
            # convierte timestamps a string
            df = df.astype(object)

            # limpia strings y normaliza tipos
            df = df.map(

                lambda x:
                    x.strftime("%Y-%m-%d")
                    if hasattr(x, "strftime")
                    else x.strip()
                    if isinstance(x, str)
                    else x
            )
            # qty_nes numeric
            if "qty_nes" in df.columns:

                df["qty_nes_numeric"] = pd.to_numeric(
                    df["qty_nes"],
                    errors="coerce"
                ).fillna(0)

                # IMPORTANTE:
                # reemplaza valores inválidos
                df["qty_nes"] = (
                    df["qty_nes_numeric"]
                    .astype(int)
                )

            else:

                df["qty_nes_numeric"] = 0
                df["qty_nes"] = 0

            # fuerza release a string
            if "release" in df.columns:

                df["release"] = (
                    df["release"]
                    .fillna("")
                    .astype(str)
                )
            imported = 0
            updated = 0

            # UPSERT lógico
            for row in df.fillna("").to_dict(orient="records"):

                system_name = row.get("sistemas", "")

                if not system_name:
                    continue

                existing = db.query(System).filter(
                    System.sistemas == system_name
                ).first()

                if existing:

                    updated += 1

                    for key, value in row.items():

                        if hasattr(existing, key):

                            setattr(existing, key, value)

                else:

                    imported += 1

                    new_system = System(**row)

                    db.add(new_system)

            db.commit()

            total_nes = int(
                df["qty_nes_numeric"].sum()
            )

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

            result.append({

                "file": file.name,

                "rows": len(df),

                "imported": imported,

                "updated": updated,

                "summary": {

                    "total_systems": len(df),

                    "total_nes": total_nes,

                    "vendors": vendors,

                    "technologies": technologies
                }
            })

        except Exception as e:

            result.append({

                "file": file.name,

                "error": str(e)
            })

    db.close()

    return result

@app.get("/api/systems")
def get_systems(

    vendor: Optional[str] = None,
    tecnologia: Optional[str] = None,
    infra: Optional[str] = None

):

    db = SessionLocal()

    query = db.query(System)

    # filtro vendor
    if vendor:

        query = query.filter(
            System.vendor == vendor
        )

    # filtro tecnologia
    if tecnologia:

        query = query.filter(
            System.tecnologia == tecnologia
        )

    # filtro infra
    if infra:

        query = query.filter(
            System.infra == infra
        )

    systems = query.all()

    db.close()

    return systems

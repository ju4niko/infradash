from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

import pandas as pd
import re
import unicodedata
from datetime import datetime
from .database import SessionLocal
from .database import engine
from .database import Base
from collections import defaultdict
from .models import System, Snapshot
from sqlalchemy import asc
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def import_excel(snapshot_date: str):

    uploads = Path("/app/data/uploads")

    files = list(uploads.glob("*.xlsx"))

    result = []

    db = SessionLocal()


    snapshot = db.query(Snapshot).filter(
        Snapshot.snapshot_date == snapshot_date
    ).first()

    if not snapshot:
        snapshot = Snapshot(
            snapshot_date=datetime.strptime(
                snapshot_date,
                "%Y-%m-%d"
            ).date()
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)



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
            df = df.drop(
                columns=["unnamed_14"],
                errors="ignore"
            )

            print("COLUMNAS ENCONTRADAS:")
            print(df.columns.tolist())

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

                row["snapshot_id"] = snapshot.id

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
    snapshot_date: Optional[str] = None,
    vendor: Optional[str] = None,
    tecnologia: Optional[str] = None,
    infra: Optional[str] = None

):

    db = SessionLocal()

    query = db.query(System)


    if snapshot_date:

        snapshot = db.query(Snapshot).filter(
            Snapshot.snapshot_date ==
            datetime.strptime(
                snapshot_date,
                "%Y-%m-%d"
            ).date()
        ).first()

        if snapshot:

            query = query.filter(
                System.snapshot_id == snapshot.id
            )



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

@app.get("/api/history")
def get_all_history():

    db = SessionLocal()

    rows = (
        db.query(
            Snapshot.snapshot_date,
            System.sistemas,
            System.qty_nes_numeric
        )
        .join(
            Snapshot,
            System.snapshot_id == Snapshot.id
        )
        .order_by(
            Snapshot.snapshot_date
        )
        .all()
    )

    db.close()

    return [
        {
            "snapshot_date": row.snapshot_date,
            "sistema": row.sistemas,
            "qty_nes": row.qty_nes_numeric
        }
        for row in rows
    ]


@app.get("/api/history/{system_name}")
def get_system_history(system_name: str):

    db = SessionLocal()

    rows = (
        db.query(
            Snapshot.snapshot_date,
            System.qty_nes_numeric
        )
        .join(
            Snapshot,
            System.snapshot_id == Snapshot.id
        )
        .filter(
            System.sistemas == system_name
        )
        .order_by(
            asc(Snapshot.snapshot_date)
        )
        .all()
    )

    db.close()

    return [
        {
            "snapshot_date": row.snapshot_date,
            "qty_nes": row.qty_nes_numeric
        }
        for row in rows
    ]

@app.get("/api/gauges")
def get_gauges():

    db = SessionLocal()

    snapshots = (
        db.query(Snapshot)
        .order_by(
            Snapshot.snapshot_date.desc()
        )
        .all()
    )

    if not snapshots:

        db.close()

        return []

    latest_snapshot = snapshots[0]

    current_systems = (
        db.query(System)
        .filter(
            System.snapshot_id == latest_snapshot.id
        )
        .all()
    )

    result = []

    for system in current_systems:

        max_qty = (
            db.query(
                System.qty_nes_numeric
            )
            .filter(
                System.sistemas == system.sistemas
            )
            .order_by(
                System.qty_nes_numeric.desc()
            )
            .first()
        )



        min_qty = (
            db.query(
                System.qty_nes_numeric
            )
            .filter(
                System.sistemas == system.sistemas
            )
            .order_by(
                System.qty_nes_numeric.asc()
            )
            .first()
        )

        historical_max = (
            max_qty[0]
            if max_qty and max_qty[0] is not None
            else 0
        )

        historical_min = (
            min_qty[0]
            if min_qty and min_qty[0] is not None
            else 0
        )

        if historical_max == historical_min:
            continue

        percentage = 0

        if historical_max > 0:

            percentage = round(
                (
                    system.qty_nes_numeric
                    / historical_max
                ) * 100,
                1
            )

        result.append({

            "sistema": system.sistemas,

            "actual": system.qty_nes_numeric,

            "maximo": historical_max,

            "porcentaje": percentage,

            "snapshot_date": latest_snapshot.snapshot_date

        })

    db.close()

    return sorted(
        result,
        key=lambda x: x["sistema"]
    )

@app.get("/api/snapshots")
def get_snapshots():

    db = SessionLocal()

    snapshots = (
        db.query(Snapshot)
        .order_by(
            Snapshot.snapshot_date.desc()
        )
        .all()
    )

    db.close()

    return [
        {
            "id": s.id,
            "snapshot_date": s.snapshot_date
        }
        for s in snapshots
    ]

@app.get("/api/trends")
def get_trends():

    db = SessionLocal()

    rows = (
        db.query(
            Snapshot.snapshot_date,
            System.sistemas,
            System.qty_nes_numeric
        )
        .join(
            Snapshot,
            System.snapshot_id == Snapshot.id
        )
        .order_by(
            Snapshot.snapshot_date.asc()
        )
        .all()
    )

    systems = defaultdict(list)

    for row in rows:

        systems[row.sistemas].append({

            "date": row.snapshot_date,

            "qty": row.qty_nes_numeric

        })

    result = []

    for system_name, history in systems.items():

        if len(history) < 2:
            continue

        n = len(history)

        x = []
        y = []

        base_date = history[0]["date"]

        for point in history:

            days = (
                point["date"]
                - base_date
            ).days

            x.append(days)

            y.append(point["qty"])

        sum_x = sum(x)
        sum_y = sum(y)

        sum_xy = sum(
            xi * yi
            for xi, yi in zip(x, y)
        )

        sum_x2 = sum(
            xi * xi
            for xi in x
        )

        denominator = (
            n * sum_x2
            - sum_x * sum_x
        )

        if denominator == 0:
            continue

        slope_per_day = (
            (
                n * sum_xy
                - sum_x * sum_y
            )
            / denominator
        )

        trend = round(
            slope_per_day * 30.44,
            2
        )

        current_value = history[-1]["qty"]

        result.append({

            "sistema": system_name,

            "actual": current_value,

            "trend": trend,

            "direction":
                "up"
                if trend > 0
                else "down"
                if trend < 0
                else "stable",

            "snapshots": n

        })

    db.close()

    return sorted(
        result,
        key=lambda x: x["sistema"]
    )


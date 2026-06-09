from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Date,
    DateTime
)

from sqlalchemy.orm import relationship

from app.database import Base


class Snapshot(Base):

    __tablename__ = "snapshots"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    snapshot_date = Column(
        Date,
        nullable=False,
        unique=True
    )

    source_file = Column(String)

    imported_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    systems = relationship(
        "System",
        back_populates="snapshot"
    )


class System(Base):

    __tablename__ = "systems"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    snapshot_id = Column(
        Integer,
        ForeignKey("snapshots.id")
    )

    imo = Column(String)
    detalles_tecnologia = Column(String)
    
    sistemas = Column(String)
    vendor = Column(String)
    soporte = Column(String)
    partner = Column(String)
    release = Column(String)

    qty_nes = Column(String)
    qty_nes_numeric = Column(Float)

    fault_manager = Column(String)
    fault_unificado_si_o_no = Column(String)

    tecnologia = Column(String)
    infra = Column(String)
    redundancia = Column(String)

    comentarios = Column(String)

    snapshot = relationship(
        "Snapshot",
        back_populates="systems"
    )

class SystemTarget(Base):

    __tablename__ = "system_targets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    sistema = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    target_date = Column(
        Date,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class SubSystem(Base):

    __tablename__ = "subsystems"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    snapshot_id = Column(
        Integer,
        ForeignKey("snapshots.id")
    )

    parent_system = Column(
        String,
        index=True
    )

    imo = Column(String)
    detalles_tecnologia = Column(String)

    sistemas = Column(String)
    vendor = Column(String)
    soporte = Column(String)
    partner = Column(String)
    release = Column(String)

    qty_nes = Column(String)
    qty_nes_numeric = Column(Float)

    fault_manager = Column(String)
    fault_unificado_si_o_no = Column(String)

    tecnologia = Column(String)
    infra = Column(String)
    redundancia = Column(String)

    comentarios = Column(String)

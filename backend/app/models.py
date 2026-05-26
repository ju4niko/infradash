from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class System(Base):

    __tablename__ = "systems"

    id = Column(Integer, primary_key=True, index=True)

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

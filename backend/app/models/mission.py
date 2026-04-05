# backend/app/models/mission.py

from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, Float, Enum as SAEnum, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

# 1. ENUM POUR LES TYPES DE CONTRATS
class TypeContratMission(str, enum.Enum):
    cddu = "CDDU"   
    ccda = "CCDA"
    both = "BOTH"

# 2. MODÈLE DE BASE DE DONNÉES (SQLAlchemy)
class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    categorie: Mapped[str] = mapped_column(String(255), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    
    type_contrat: Mapped[TypeContratMission] = mapped_column(
        SAEnum(TypeContratMission, name="type_contrat_mission_enum"),
        default=TypeContratMission.ccda,
        nullable=False
    )
    
    tarif_unitaire: Mapped[float] = mapped_column(Float, nullable=False)
    unite: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Tes toggles d'accès magiques
    dispo_resp: Mapped[bool] = mapped_column(Boolean, default=True)
    dispo_tcp: Mapped[bool] = mapped_column(Boolean, default=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Dates auto-gérées
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
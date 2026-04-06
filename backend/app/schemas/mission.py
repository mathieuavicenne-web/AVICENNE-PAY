# backend/app/schemas/mission.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
# On importe l'Enum depuis le dossier models pour garder une source unique de vérité !
from app.models.mission import TypeContratMission

# ─── SCHÉMA DE BASE (Partagé) ──────────────────────────────────────────
class MissionBase(BaseModel):
    categorie: str = Field(..., min_length=2, max_length=255, description="Ex: ✍️ Rédiger et mettre en page...")
    titre: str = Field(..., min_length=2, max_length=255, description="Ex: LVL 1 - Pas ou peu de changements")
    type_contrat: TypeContratMission = TypeContratMission.ccda
    tarif_unitaire: float = Field(..., ge=0, description="Le tarif ne peut pas être négatif")
    unite: str = Field(..., min_length=1, max_length=100, description="Ex: par qcm")
    
    # Tes deux toggles bien explicites !
    dispo_resp: bool = Field(True, description="Accessible aux Responsables (RESP)")
    dispo_tcp: bool = Field(True, description="Accessible aux Tuteurs/Trices (TCP)")
    
    is_active: bool = True

# ─── SCHÉMA POUR LA CRÉATION (Input API) ────────────────────────────────
class MissionCreate(MissionBase):
    pass

# ─── SCHÉMA POUR LA MISE À JOUR (Input API) ────────────────────────────
class MissionUpdate(BaseModel):
    categorie: Optional[str] = None
    titre: Optional[str] = None
    type_contrat: Optional[TypeContratMission] = None
    tarif_unitaire: Optional[float] = None
    unite: Optional[str] = None
    dispo_resp: Optional[bool] = None
    dispo_tcp: Optional[bool] = None
    is_active: Optional[bool] = None

# ─── SCHÉMA POUR LA RÉPONSE (Output API) ───────────────────────────────
class MissionResponse(MissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
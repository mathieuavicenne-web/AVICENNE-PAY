from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.declaration import StatutDeclaration

# ── 1. SCHÉMAS POUR LES LIGNES ──────────────────────────────────────────────

class LigneDeclarationCreate(BaseModel):
    mission_id: int
    quantite: float = Field(..., gt=0, description="La quantité doit être supérieure à 0")


class LigneDeclarationOut(BaseModel):
    id: int
    declaration_id: int
    mission_id: int
    quantite: float
    tarif_applique: float

    @property
    def sous_total(self) -> float:
        return round(self.quantite * self.tarif_applique, 2)

    model_config = ConfigDict(from_attributes=True)


# ── 2. SCHÉMAS POUR L'UTILISATEUR (La solution à ton problème) ──────────────

class UserMinimalOut(BaseModel):
    prenom: Optional[str] = None
    nom: Optional[str] = None
    site: Optional[str] = None
    role: Optional[str] = None
    programme: Optional[str] = None
    matiere: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── 3. SCHÉMAS POUR LA DÉCLARATION ──────────────────────────────────────────

class DeclarationCreate(BaseModel):
    mois: int = Field(..., ge=1, le=12)
    annee: int = Field(..., ge=2025)
    lignes: List[LigneDeclarationCreate] = Field(..., min_length=1)


class DeclarationOut(BaseModel):
    id: int
    user_id: int
    mois: int
    annee: int
    statut: StatutDeclaration
    commentaire_refus: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lignes: List[LigneDeclarationOut]
    total_remuneration: float 
    
    # 🎯 FastAPI va maintenant chercher l'objet User complet
    user: Optional[UserMinimalOut] = None

    model_config = ConfigDict(from_attributes=True)


class DeclarationUpdate(BaseModel):
    mois: Optional[int] = Field(None, ge=1, le=12)
    annee: Optional[int] = Field(None, ge=2025)
    lignes: Optional[List[LigneDeclarationCreate]] = Field(None, min_length=1)


class DeclarationReview(BaseModel):
    statut: StatutDeclaration
    commentaire_refus: Optional[str] = Field(None, max_length=500)
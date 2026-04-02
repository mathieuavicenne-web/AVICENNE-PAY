# backend/app/schemas/declaration.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field, ConfigDict
from app.models.declaration import StatutDeclaration
from app.schemas.ligne_declaration import LigneDeclarationOut

# ── 1. SCHÉMAS POUR LES LIGNES ──────────────────────────────────────────────
    
# Ce que l'utilisateur envoie pour une ligne
class LigneDeclarationCreate(BaseModel):
    mission_id: int
    quantite: float = Field(..., gt=0, description="La quantité (heures, QCM, etc.) doit être supérieure à 0")

# ── 2. SCHÉMAS POUR LA DÉCLARATION ──────────────────────────────────────────

# Ce que l'utilisateur envoie pour créer une déclaration
class DeclarationCreate(BaseModel):
    mois: int = Field(..., ge=1, le=12, description="Le mois doit être compris entre 1 et 12")
    annee: int = Field(..., ge=2025, description="L'année de la déclaration")
    lignes: List[LigneDeclarationCreate] = Field(..., min_length=1, description="Il faut au moins déclarer une mission")

# Ce que l'API renvoie quand on consulte une déclaration
class DeclarationOut(BaseModel):
    id: int
    user_id: int
    mois: int
    annee: int
    statut: StatutDeclaration
    commentaire_refus: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # On imbrique la liste des lignes
    lignes: List[LigneDeclarationOut]
    
    # Grâce à ta super @property dans le modèle SQLAlchemy !
    total_remuneration: float 

    # backend/app/schemas/ligne_declaration.py

from pydantic import BaseModel, computed_field, ConfigDict

class LigneDeclarationOut(BaseModel):
    id: int
    declaration_id: int
    mission_id: int
    quantite: float
    tarif_applique: float

    # 💡 Pydantic v2 calcule automatiquement ce champ à la volée !
    @computed_field
    def sous_total(self) -> float:
        return round(self.quantite * self.tarif_applique, 2)

    model_config = ConfigDict(from_attributes=True)

class DeclarationUpdate(BaseModel):
    mois: Optional[int] = Field(None, ge=1, le=12)
    annee: Optional[int] = Field(None, ge=2025)
    lignes: Optional[List[LigneDeclarationCreate]] = Field(None, min_length=1)

class DeclarationReview(BaseModel):
    statut: StatutDeclaration
    commentaire_refus: Optional[str] = Field(None, max_length=500)
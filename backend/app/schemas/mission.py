# backend/app/schemas/mission.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.mission import TypeContratMission

# Base commune
class MissionBase(BaseModel):
    categorie: str
    titre: str
    type_contrat: TypeContratMission = TypeContratMission.ccda
    tarif_unitaire: float = Field(..., gt=0)
    unite: str
    is_resp_only: bool = False
    is_active: bool = True

# Pour la création (Admin)
class MissionCreate(MissionBase):
    pass

# Pour la mise à jour (Admin)
class MissionUpdate(BaseModel):
    categorie: Optional[str] = None
    titre: Optional[str] = None
    type_contrat: Optional[TypeContratMission] = None
    tarif_unitaire: Optional[float] = Field(None, gt=0)
    unite: Optional[str] = None
    is_resp_only: Optional[bool] = None
    is_active: Optional[bool] = None

# Ce que l'API renvoie
class MissionOut(MissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

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
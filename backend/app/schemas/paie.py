# backend/app/schemas/paie.py

from pydantic import BaseModel, ConfigDict
from typing import List

# ─── 🧾 PARTIE 1 : SYNTHÈSE DE PAIE (Déjà présente) ───────────────────
class LigneSynthesePaie(BaseModel):
    user_id: int
    nom: str
    prenom: str
    site: str
    total_missions: int
    montant_brut_total: float

    model_config = ConfigDict(from_attributes=True)


class SynthesePaieOut(BaseModel):
    mois: int
    annee: int
    total_intervenants: int
    montant_global: float
    details: List[LigneSynthesePaie]

    model_config = ConfigDict(from_attributes=True)


# ─── 📊 PARTIE 2 : PILOTAGE & ANALYSES (À ajouter) ───────────────────
class MensualiteDepense(BaseModel):
    mois: int
    depenses_ccda: float
    depenses_ccdu: float

    model_config = ConfigDict(from_attributes=True)


class PilotageDepensesResponse(BaseModel):
    annee: int
    donnees: List[MensualiteDepense]

    model_config = ConfigDict(from_attributes=True)
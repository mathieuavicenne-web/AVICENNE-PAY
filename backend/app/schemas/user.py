from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from app.core.referentiels import MATIERES, Role, Site, TypeContrat

# ── 1. LE SCHÉMA DE BASE (Champs communs) ───────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None


# ── 📦 CLASSE INTERMÉDIAIRE (Pour mutualiser les validateurs) ────────────────
class UserPedago(BaseModel):
    """
    Classe utilitaire pour centraliser la validation du couple Programme/Matière.
    """
    programme: Optional[str] = None
    matiere: Optional[str] = None

    @field_validator("programme")
    @classmethod
    def validate_programme(cls, v: str):
        if v and v not in MATIERES.keys():
            raise ValueError(f"Le programme doit être l'un des suivants : {list(MATIERES.keys())}")
        return v

    @field_validator("matiere")
    @classmethod
    def validate_matiere(cls, v: str, values):
        # Récupération sécurisée des données de la requête
        programme_saisi = values.data.get("programme")
        
        if v and programme_saisi:
            matieres_possibles = MATIERES.get(programme_saisi, [])
            if v not in matieres_possibles:
                raise ValueError(f"La matière '{v}' n'existe pas pour le programme '{programme_saisi}'.")
        return v


# ── 2. INSCRIPTION / CRÉATION ───────────────────────────────────────────────
# 💡 Hérite de UserBase ET de UserPedago !
class UserCreate(UserBase, UserPedago):
    password: str = Field(..., min_length=6)
    role: Role = Role.admin
    site: Optional[Site] = None


# ── 3. MISE À JOUR PAR L'UTILISATEUR (Son Profil) ──────────────────────────
class UserProfileUpdate(BaseModel):
    """
    Champs que l'utilisateur lambda peut modifier lui-même.
    """
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    
    # 🇫🇷 Validation NSS : 15 chiffres
    nss: Optional[str] = Field(None, pattern=r"^[12]\d{14}$") 
    
    # 🏦 Validation IBAN FR
    iban: Optional[str] = Field(None, pattern=r"^FR\d{2}[A-Z0-9]{4}\d{7}[A-Z0-9]{10}\d{2}$")

    model_config = ConfigDict(str_strip_whitespace=True)


# ── 4. MISE À JOUR PAR L'ADMIN ──────────────────────────────────────────────
# 💡 Hérite de UserProfileUpdate ET de UserPedago !
class UserUpdate(UserProfileUpdate, UserPedago):
    """
    L'admin hérite de tout ce que le user peut modifier, 
    mais lui peut toucher au pro (rôle, etc).
    """
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    site: Optional[Site] = None
    password: Optional[str] = Field(None, min_length=6)


# ── 5. SORTIE (Ce que l'API renvoie au Front) ──────────────────────────────
class UserOut(UserBase):
    id: int
    role: Role
    is_active: bool
    site: Optional[Site] = None
    programme: Optional[str] = None
    matiere: Optional[str] = None
    profil_complete: bool
    type_contrat: Optional[TypeContrat] = None 
    
    # 🔒 On ajoute ces deux lignes pour rassurer le Front-end !
    nss: Optional[str] = None
    iban: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── 6. SÉCURITÉ MOTS DE PASSE ──────────────────────────────────────────────
class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class AdminPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6)
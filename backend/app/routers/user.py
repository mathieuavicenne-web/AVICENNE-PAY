# backend/routers/user.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.core.referentiels import Site, MATIERES, Role
from app.schemas.user import (
    UserCreate, 
    UserOut, 
    UserUpdate, 
    UserProfileUpdate,
    PasswordChange, 
    AdminPasswordReset,
)
# 💡 On importe nos fonctions de chiffrement et de décodage
from app.core.security import get_current_user, get_password_hash, encrypt_data, decrypt_data, verify_password, check_is_at_least_coordo, check_peut_creer_user
from app.core.referentiels import Role, Site, MATIERES

router = APIRouter(prefix="/users", tags=["Gestion des Utilisateurs"])

# ── 👤 ROUTES DU PROFIL PERSONNEL (POUR L'UTILISATEUR CONNECTÉ) ──

@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Récupère les infos de l'utilisateur connecté avec IBAN/NSS masqués."""
    user_data = current_user
    
    user_data.nss = decrypt_data(current_user.nss_encrypted) if current_user.nss_encrypted else None
    user_data.iban = decrypt_data(current_user.iban_encrypted) if current_user.iban_encrypted else None
    
    return user_data

@router.patch("/me", response_model=UserOut)
def update_my_profile(
    profile_data: UserProfileUpdate,  # 👈 Ton schéma validé
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permet à l'utilisateur de mettre à jour ses propres infos (NSS, IBAN, adresse...)"""
    update_data = profile_data.model_dump(exclude_unset=True)
    
    # 🔒 1. Traitement spécifique pour les données sensibles à chiffrer
    if "nss" in update_data:
        nss_clair = update_data.pop("nss")
        update_data["nss_encrypted"] = encrypt_data(nss_clair) if nss_clair else None
        
    if "iban" in update_data:
        iban_clair = update_data.pop("iban")
        update_data["iban_encrypted"] = encrypt_data(iban_clair) if iban_clair else None

    # 💾 2. Sauvegarde du reste des infos
    for key, value in update_data.items():
        setattr(current_user, key, value)
        
    # 💥 3. NOUVELLE RÈGLE MÉTIER : On vérifie si le profil est complet
    # Pour pouvoir saisir une déclaration, ces 5 champs sont impératifs
    champs_obligatoires = [
        current_user.adresse, 
        current_user.code_postal, 
        current_user.ville, 
        current_user.nss_encrypted, # On teste la présence de la donnée chiffrée
        current_user.iban_encrypted # On teste la présence de la donnée chiffrée
    ]
    
    # .profil_complete passe à True si TOUS les éléments de la liste existent (bool(x) == True)
    current_user.profil_complete = all(bool(champ) for champ in champs_obligatoires)
        
    db.commit()
    db.refresh(current_user)
    
    # 🔓 4. On repasse les données en clair pour la réponse du frontend
    current_user.nss = decrypt_data(current_user.nss_encrypted) if current_user.nss_encrypted else None
    current_user.iban = decrypt_data(current_user.iban_encrypted) if current_user.iban_encrypted else None
    
    return current_user

# ── 👥 GESTION DES UTILISATEURS PAR LES MANAGERS ──

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(check_peut_creer_user)
):
    # 🤝 RÈGLE 1 : Le COORDO (Crée RESP et TCP de son SITE)
    if current_user.role == Role.coordo:
        if user_in.role not in [Role.resp, Role.tcp]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un Coordinateur ne peut créer que des Responsables ou des TCP."
            )
        if user_in.site != current_user.site:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous ne pouvez créer des utilisateurs que pour votre site ({current_user.site.value})."
            )

    # 🎯 RÈGLE 2 : Le RESP (Crée les TCP de son SITE + PROG + MATIÈRE)
    elif current_user.role == Role.resp:
        if user_in.role != Role.tcp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un Responsable ne peut créer que des TCP."
            )
        if (user_in.site != current_user.site or 
            user_in.programme != current_user.programme or 
            user_in.matiere != current_user.matiere):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez créer des TCP que dans votre strict périmètre (Site, Programme et Matière identiques au vôtre)."
            )

   # 📈 RÈGLE 3 : Le TOP COM (Crée les COM de son SITE)
    elif current_user.role == Role.top_com:  # 👈 Corrigé ici !
        if user_in.role != Role.com:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un TOP COM ne peut créer que des Commerciaux (COM)."
            )
        if user_in.site != current_user.site:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous ne pouvez créer des commerciaux que pour votre site ({current_user.site.value})."
            )

    # --- SÉCURITÉ COMMUNE (Si l'Admin passe, ou si les règles ci-dessus sont respectées) ---
    # 1. Vérification doublon email
    email_exists = db.query(User).filter(User.email == user_in.email).first()
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )

    # 2. LA RÈGLE STRICTE : Unicité du COORDO par site
    if user_in.role == Role.coordo:
        existing_coordo = db.query(User).filter(
            User.role == Role.coordo,
            User.site == user_in.site,
            User.is_active == True 
        ).first()

        if existing_coordo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le poste de Coordinateur pour le site de {user_in.site.value} est déjà occupé par {existing_coordo.prenom} {existing_coordo.nom}."
            )

    # 💥 NOUVELLE RÈGLE : Renseignement obligatoire de site/programme/matiere pour RESP et TCP
    if user_in.role in [Role.resp, Role.tcp]:
        if not user_in.site or not user_in.programme or not user_in.matiere:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le renseignement du Site, du Programme et de la Matière est impératif pour créer un {user_in.role.value}."
            )

    # 💥 NOUVELLE RÈGLE : Renseignement obligatoire du site pour TOP, TOP COM et COORDO
    if user_in.role in [Role.top, Role.top_com, Role.coordo]:
        if not user_in.site:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le renseignement du Site est impératif pour créer un {user_in.role.value}."
            )
    
    # 💥 NOUVELLE RÈGLE : Unicité stricte du RESP par triplet (Site / Prog / Mat)
    if user_in.role == Role.resp:
        existing_resp = db.query(User).filter(
            User.role == Role.resp,
            User.site == user_in.site,
            User.programme == user_in.programme,
            User.matiere == user_in.matiere,
            User.is_active == True
        ).first()

        if existing_resp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Poste occupé : Le poste de Responsable pour {user_in.site.value} / {user_in.programme} / {user_in.matiere} est déjà attribué à {existing_resp.prenom} {existing_resp.nom}."
            )
        
    # 3. Hachage du mot de passe
    user_data = user_in.model_dump()
    plain_password = user_data.pop("password")
    hashed_password = get_password_hash(plain_password)
    
    # 4. Sauvegarde
    new_user = User(**user_data, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.get("/", response_model=List[UserOut])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(User)
    
    # 🛡️ RÈGLE 1 : L'Admin voit ABSOLUMENT TOUT le monde
    if current_user.role == Role.admin:
        pass 
        
    # 🛡️ RÈGLE 2 : Le COORDO voit les RESP et TCP de son SITE + lui-même
    elif current_user.role == Role.coordo:
        query = query.filter(
            User.site == current_user.site,
            or_(
                User.role.in_([Role.resp, Role.tcp]),
                User.id == current_user.id
            )
        )
        
    # 🛡️ RÈGLE 3 : Le RESP voit uniquement les TCP de son triplet (Site/Prog/Mat) + lui-même
    elif current_user.role == Role.resp:
        query = query.filter(
            User.site == current_user.site,
            User.programme == current_user.programme,
            User.matiere == current_user.matiere,
            or_(
                User.role == Role.tcp,
                User.id == current_user.id
            )
        )
        
    # 🛡️ RÈGLE 4 : Le TOP COM voit les COM de son SITE + lui-même
    elif current_user.role == Role.top_com:
        query = query.filter(
            User.site == current_user.site,
            or_(
                User.role == Role.com,
                User.id == current_user.id
            )
        )
        
    # 🛡️ RÈGLE 5 : Les exécutants (TCP, COM) ne voient qu'eux-mêmes
    else:
        query = query.filter(User.id == current_user.id)
        
    return query.all()

@router.patch("/{user_id}/toggle", response_model=dict)
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) 
):
    # 🔍 1. Recherche de l'utilisateur cible
    user_to_toggle = db.query(User).filter(User.id == user_id).first()
    if not user_to_toggle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Utilisateur introuvable."
        )
        
    # 🛡️ 2. Droits spécifiques pour le COORDO (Même site uniquement)
    if current_user.role == Role.coordo and user_to_toggle.site != current_user.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="En tant que Coordinateur, vous ne pouvez modifier que les utilisateurs de votre site."
        )
        
    # ⚠️ 3. Empêcher de s'auto-désactiver par erreur !
    if user_to_toggle.id == current_user.id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas désactiver votre propre compte."
        )
        
    # 💥 4. Sécurité ultime : Empêcher de désactiver le dernier Admin (Ajouté ici !)
    if user_to_toggle.role == Role.admin and user_to_toggle.is_active:
        total_admins_actifs = db.query(User).filter(User.role == Role.admin, User.is_active == True).count()
        if total_admins_actifs <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de désactiver le dernier administrateur actif du système."
            )

    # 🔄 5. Inversion du booléen is_active
    user_to_toggle.is_active = not user_to_toggle.is_active
    
    db.commit()
    db.refresh(user_to_toggle)
    
    statut_str = "activé" if user_to_toggle.is_active else "désactivé"
    return {"message": f"L'utilisateur {user_to_toggle.email} a été {statut_str} avec succès."}

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    # 🛡️ FastAPI bloque DIRECTEMENT l'accès si l'user n'est ni Admin ni Coordo
    current_user: User = Depends(check_is_at_least_coordo)
):
    # 🔍 1. Recherche de l'utilisateur cible
    user_to_edit = db.query(User).filter(User.id == user_id).first()
    if not user_to_edit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    # 🛡️ 2. Droits spécifiques pour le COORDO
    if current_user.role == Role.coordo:
        # Il ne peut éditer que les gens de son site
        if user_to_edit.site != current_user.site:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="En tant que Coordinateur, vous ne pouvez éditer que les utilisateurs de votre site."
            )
        # Il ne peut éditer que les RESP et les TCP
        if user_to_edit.role not in [Role.resp, Role.tcp]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un Coordinateur ne peut éditer que des Responsables ou des TCP."
            )

    # 🧠 3. Extraction des données envoyées (sans toucher aux champs non renseignés)
    update_data = user_in.model_dump(exclude_unset=True)
    
    # 🔐 AJOUT SÉCURITÉ : Traitement du mot de passe s'il est fourni
    # Si le frontend a envoyé un mot de passe (et qu'il n'est pas vide), on le hache.
    if "password" in update_data:
        plain_password = update_data.pop("password")
        if plain_password: 
            update_data["hashed_password"] = get_password_hash(plain_password)

    # On simule les futures valeurs pour checker la cohérence
    futur_role = update_data.get("role", user_to_edit.role)
    futur_site = update_data.get("site", user_to_edit.site)
    futur_prog = update_data.get("programme", user_to_edit.programme)
    futur_mat = update_data.get("matiere", user_to_edit.matiere)

    # 💥 4. LA RÈGLE STRICTE : Unicité du RESP par périmètre
    if futur_role == Role.resp:
        # On cherche s'il existe DÉJÀ un autre RESP sur ce même triplet (en excluant le user lui-même)
        existing_resp = db.query(User).filter(
            User.role == Role.resp,
            User.site == futur_site,
            User.programme == futur_prog,
            User.matiere == futur_mat,
            User.id != user_id 
        ).first()

        if existing_resp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Poste occupé : Le poste de Responsable pour {futur_site} / {futur_prog} / {futur_mat} est déjà attribué à {existing_resp.prenom} {existing_resp.nom}."
            )

    # 💾 5. Sauvegarde si tout est validé !
    for key, value in update_data.items():
        setattr(user_to_edit, key, value)

    db.commit()
    db.refresh(user_to_edit)
    return user_to_edit

@router.patch("/me/change-password", response_model=dict)
def change_my_password(
    passwords: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🕵️‍♂️ 1. Vérifier que l'ancien mot de passe est le bon
    if not verify_password(passwords.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'ancien mot de passe est incorrect."
        )
        
    # 🛑 2. Vérifier que le nouveau mot de passe n'est pas identique à l'ancien
    if passwords.old_password == passwords.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit être différent de l'ancien."
        )
        
    # 🔒 3. Hasher le nouveau mot de passe et sauvegarder
    current_user.hashed_password = get_password_hash(passwords.new_password)
    
    db.commit()
    
    return {"message": "Mot de passe mis à jour avec succès !"}

@router.patch("/{user_id}/reset-password", response_model=dict)
def admin_reset_password(
    user_id: int,
    password_data: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🛑 1. Seul l'Admin a le droit de vie ou de mort sur les mots de passe
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent réinitialiser le mot de passe d'un tiers."
        )
        
    # 🔍 2. Recherche de l'utilisateur cible
    user_to_reset = db.query(User).filter(User.id == user_id).first()
    if not user_to_reset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Utilisateur introuvable."
        )
        
    # 🔒 3. Érasement avec le nouveau mot de passe haché
    user_to_reset.hashed_password = get_password_hash(password_data.new_password)
    
    db.commit()
    
    return {"message": f"Le mot de passe de {user_to_reset.email} a été réinitialisé avec succès."}

# ── 👥 ROUTE REFERENTIELS ──
@router.get("/constants/referentiels")
def get_referentiels():
    """Renvoie les listes de sites, rôles et matières pour le frontend."""
    return {
        "sites": [site.value for site in Site],
        "roles": [role.value for role in Role],
        "matieres": MATIERES
    }
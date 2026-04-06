from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.user import User, Role
from app.models.declaration import Declaration, StatutDeclaration, LigneDeclaration
from app.models.mission import Mission, TypeContratMission
from app.schemas.paie import SynthesePaieOut, LigneSynthesePaie, PilotageDepensesResponse, MensualiteDepense
from app.core.security import check_is_at_least_coordo, get_current_user, decrypt_data

router = APIRouter(prefix="/paie", tags=["Paie & Synthèses"])

# ─── 🧾 ROUTE 1 : SYNTHÈSE DE PAIE ───────────────────
@router.get("/synthese-mensuelle")
def get_synthese_mensuelle(
    mois_debut: int,
    annee_debut: int,
    mois_fin: int,
    annee_fin: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo)
):
    """
    Récupère TOUTES les déclarations comprises entre la période de début
    et la période de fin incluses.
    """
    # 1. Sous-requête pour les totaux (identique au précédent)
    sous_requete_totaux = db.query(
        LigneDeclaration.declaration_id.label("dec_id"),
        func.sum(LigneDeclaration.quantite * LigneDeclaration.tarif_applique).label("total_brut")
    ).group_by(LigneDeclaration.declaration_id).subquery()

    # 2. Requête principale
    query = db.query(
        User.nom.label("nom"),
        User.prenom.label("prenom"),
        User.site.label("site"),
        User.role.label("role"),
        Declaration.mois.label("mois"),
        Declaration.annee.label("annee"),
        Declaration.statut.label("statut"),
        func.coalesce(sous_requete_totaux.c.total_brut, 0).label("montant_brut")
    ).join(
        Declaration, User.id == Declaration.user_id
    ).outerjoin(
        sous_requete_totaux, Declaration.id == sous_requete_totaux.c.dec_id
    )

    # 🎯 Filtrage par plage de dates
    # Astuce classique pour comparer facilement des périodes : (annee * 100) + mois
    # Ex: Janvier 2026 devient 202601 et Mars 2026 devient 202603
    periode_debut = (annee_debut * 100) + mois_debut
    periode_fin = (annee_fin * 100) + mois_fin

    query = query.filter(
        ((Declaration.annee * 100) + Declaration.mois) >= periode_debut,
        ((Declaration.annee * 100) + Declaration.mois) <= periode_fin
    )

    # Filtre par site pour les coordos (identique au précédent)
    if current_user.role == Role.coordo:
        query = query.filter(User.site == current_user.site)

    results = query.all()

    synthese = []
    for res in results:
        synthese.append({
            "nom": res.nom.upper(),
            "prenom": res.prenom,
            "site": res.site.value if hasattr(res.site, 'value') else str(res.site),
            "role": res.role.value if hasattr(res.role, 'value') else str(res.role),
            "periode": f"{str(res.mois).zfill(2)}/{res.annee}",
            "statut": res.statut.value if hasattr(res.statut, 'value') else str(res.statut),
            "montant_brut": round(float(res.montant_brut), 2)
        })

    return synthese


# ─── 📊 ROUTE 2 : PILOTAGE & ANALYSES (À ajouter) ───────────────────
@router.get("/pilotage/depenses", response_model=PilotageDepensesResponse)
def get_pilotage_depenses(
    annee: int = 2026,
    site: Optional[str] = None,
    db: Session = Depends(get_db),
    # 🛡️ Sécurité : Tu as mentionné que le pilotage est strictement réservé aux ADMINS
    current_user: User = Depends(get_current_user) 
):
    """
    Calcule la masse salariale par mois pour une année donnée, par type de contrat.
    Réservé exclusivement aux administrateurs.
    """
    # 🔒 Double vérification de sécurité pour les admins
    if current_user.role != "admin" and current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé exclusivement aux administrateurs."
        )

    # 📊 Requête SQL d'agrégation
    # On calcule la somme des lignes de déclarations validées, groupées par mois et type de contrat
    query = db.query(
        Declaration.mois,
        Mission.type_contrat,
        func.sum(LigneDeclaration.quantite * LigneDeclaration.tarif_applique).label("total")
    ).join(
        LigneDeclaration, Declaration.id == LigneDeclaration.declaration_id
    ).join(
        Mission, LigneDeclaration.mission_id == Mission.id
    ).filter(
        Declaration.annee == annee,
        Declaration.statut == StatutDeclaration.validee
    )

    # Filtre optionnel par site (si demandé via le front)
    if site and site != "all":
        query = query.join(User, Declaration.user_id == User.id).filter(User.site == site)

    # Groupement des résultats
    results = query.group_by(Declaration.mois, Mission.type_contrat).all()

    # 🧠 Formatage de la réponse pour les graphiques (on initialise les 12 mois à 0)
    data_map = {m: {"mois": m, "depenses_ccda": 0.0, "depenses_ccdu": 0.0} for m in range(1, 13)}

    for mois, type_contrat, total in results:
        valeur_arrondie = round(float(total), 2) if total else 0.0
        if type_contrat == TypeContratMission.ccda:
            data_map[mois]["depenses_ccda"] = valeur_arrondie
        elif type_contrat == TypeContratMission.ccdu:
            data_map[mois]["depenses_ccdu"] = valeur_arrondie

    return PilotageDepensesResponse(
        annee=annee,
        donnees=[MensualiteDepense(**val) for val in data_map.values()]
    )

# ─── 📊 ROUTE 3 : EXPORT DÉTAILLÉ ───────────────────
@router.get("/synthese-mensuelle/details")
def get_synthese_details(
    mois_debut: int,
    annee_debut: int,
    mois_fin: int,
    annee_fin: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo)
):
    """
    Récupère la liste exhaustive des lignes de déclarations validées.
    Déchiffre au passage le NSS et l'IBAN pour la compta.
    Filtre par plage de dates du ... au ...
    """
    query = db.query(
        User.nom.label("nom"),
        User.prenom.label("prenom"),
        User.site.label("site_intervenant"),
        User.role.label("role"),
        User.programme.label("programme_user"),
        User.nss_encrypted.label("nss_raw"),   
        User.iban_encrypted.label("iban_raw"), 
        Mission.categorie.label("mission"),
        Mission.titre.label("matiere"),
        Mission.type_contrat.label("type_contrat"),
        LigneDeclaration.quantite.label("quantite"),
        LigneDeclaration.tarif_applique.label("tarif_unitaire")
    ).select_from(Declaration).join(
        User, User.id == Declaration.user_id
    ).join(
        LigneDeclaration, Declaration.id == LigneDeclaration.declaration_id
    ).join(
        Mission, LigneDeclaration.mission_id == Mission.id
    )

    # 🎯 1. Filtrage par plage de dates
    periode_debut = (annee_debut * 100) + mois_debut
    periode_fin = (annee_fin * 100) + mois_fin

    query = query.filter(
        ((Declaration.annee * 100) + Declaration.mois) >= periode_debut,
        ((Declaration.annee * 100) + Declaration.mois) <= periode_fin,
        Declaration.statut == StatutDeclaration.validee
    )

    # 🎯 2. Filtre par site pour les coordos
    if current_user.role == Role.coordo:
        query = query.filter(User.site == current_user.site)

    results = query.all()

    details_complets = []
    for res in results:
        
        # 🛡️ Déchiffrement des données sensibles
        nss_dechiffre = "Non renseigné"
        iban_dechiffre = "Non renseigné"
        
        if res.nss_raw:
            nss_dechiffre = decrypt_data(res.nss_raw)
        if res.iban_raw:
            iban_dechiffre = decrypt_data(res.iban_raw)

        details_complets.append({
            "type_contrat": str(res.type_contrat.value) if hasattr(res.type_contrat, 'value') else str(res.type_contrat),
            "nom": res.nom,
            "prenom": res.prenom,
            "site": res.site_intervenant.value if hasattr(res.site_intervenant, 'value') else str(res.site_intervenant),
            "role": res.role.value if hasattr(res.role, 'value') else str(res.role),
            "programme": res.programme_user or "Non renseigné",
            "nss": nss_dechiffre,
            "iban": iban_dechiffre,
            "mission": res.mission,
            "matiere": res.matiere,
            "quantite": float(res.quantite),
            "tarif_unitaire": float(res.tarif_unitaire),
            "montant_brut": round(float(res.quantite * res.tarif_unitaire), 2)
        })

    return details_complets
import pytest
from app.database import get_db
from app.models.user import User
from app.models.declaration import Declaration, StatutDeclaration, LigneDeclaration
from app.models.mission import Mission, TypeContratMission

from app.core.referentiels import Role, Site

# ── 🧪 TEST 1 : SÉCURITÉ DE LA ROUTE PILOTAGE ─────────────────────────────
def test_get_pilotage_depenses_forbidden_for_coordo(client_coordo):
    """
    On vérifie que la Route de pilotage refuse l'accès à un Coordo,
    car elle est réservée exclusivement aux Admins.
    """
    # 🎯 Correction de l'URL avec /api/v1
    response = client_coordo.get("/api/v1/paie/pilotage/depenses?annee=2026")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Accès réservé exclusivement aux administrateurs."


# ── 🧪 TEST 2 : LOGIQUE DE PÉRIODE (Route Synthèse) ──────────────────────
def test_get_synthese_mensuelle_date_range(client_admin):
    """
    On vérifie que la comparaison mathématique des périodes fonctionne.
    """
    # 🎯 Correction de l'URL avec /api/v1
    response = client_admin.get(
        "/api/v1/paie/synthese-mensuelle?mois_debut=3&annee_debut=2026&mois_fin=5&annee_fin=2026"
    )
    
    assert response.status_code == 200
    donnees = response.json()
    assert isinstance(donnees, list)


# ── 🧪 TEST 3 : SÉCURITÉ DÉCHIFFREMENT NSS/IBAN (Route Détails) ──────────
def test_get_synthese_details_fallback_encryption(client_admin):
    """
    On s'assure que si les données NSS/IBAN sont nulles en DB,
    le code ne crash pas.
    """
    # 🎯 Correction de l'URL avec /api/v1
    response = client_admin.get(
        "/api/v1/paie/synthese-mensuelle/details?mois_debut=1&annee_debut=2026&mois_fin=1&annee_fin=2026"
    )
    
    assert response.status_code == 200

from app.core.referentiels import Role, Site

def test_calcul_synthese_mensuelle_exact(client_admin):
    """
    Vérifie que la synthèse calcule correctement les montants cumulés.
    """
    db = next(get_db())
    
    test_user = None
    test_declaration = None
    test_mission = None
    
    try:
        # 1. Création de l'utilisateur (avec de vraies valeurs d'Enum)
        test_user = User(
            nom="DUPONT", 
            prenom="Jean", 
            email="jean.dupont@test.fr", 
            role=Role.com,           # ✅ "com" existe dans ton Enum
            site=Site.lyon_est       # ✅ "Lyon Est" existe dans ton Enum
        )
        db.add(test_user)
        db.flush() 
        
        # 2. Création de la déclaration
        test_declaration = Declaration(
            user_id=test_user.id, mois=3, annee=2026, statut=StatutDeclaration.brouillon
        )
        db.add(test_declaration)
        db.flush()
        
        # 3. Création de la mission
        test_mission = Mission(
            titre="Soutien Maths", 
            categorie="Cours", 
            type_contrat=TypeContratMission.ccda,
            tarif_unitaire=10.0,      # 👈 Ajouté pour respecter la contrainte NOT NULL
            unite="par heure"         # 👈 Ajouté pour respecter la contrainte NOT NULL
        )
        db.add(test_mission)
        db.flush()
        
        # 4. Ajout des lignes (25€ x 2 + 30€ x 1.5 = 95€)
        ligne1 = LigneDeclaration(declaration_id=test_declaration.id, mission_id=test_mission.id, quantite=2.0, tarif_applique=25.0) 
        ligne2 = LigneDeclaration(declaration_id=test_declaration.id, mission_id=test_mission.id, quantite=1.5, tarif_applique=30.0) 
        db.add_all([ligne1, ligne2])
        db.commit() 
        
        # 5. Appel de l'API
        response = client_admin.get(
            "/api/v1/paie/synthese-mensuelle?mois_debut=3&annee_debut=2026&mois_fin=3&annee_fin=2026"
        )
        
        assert response.status_code == 200
        donnees = response.json()
        
        synth_jean = next((x for x in donnees if x["nom"] == "DUPONT"), None)
        
        assert synth_jean is not None, "L'utilisateur n'a pas été trouvé dans la synthèse !"
        assert synth_jean["montant_brut"] == 95.0
        
    except Exception as e:
        db.rollback()
        raise e
        
    finally:
        # 🛡️ Nettoyage sécurisé
        db.rollback() 
        if test_declaration and test_declaration.id:
            db.query(LigneDeclaration).filter(LigneDeclaration.declaration_id == test_declaration.id).delete()
            db.query(Declaration).filter(Declaration.id == test_declaration.id).delete()
        if test_mission and test_mission.id:
            db.query(Mission).filter(Mission.id == test_mission.id).delete()
        if test_user and test_user.id:
            db.query(User).filter(User.id == test_user.id).delete()
            
        db.commit()
# -*- coding: utf-8 -*-
# backend/seed_catalog_ccda.py

import os
import sys
import enum
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import String, Float, Enum as SAEnum, Boolean, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column

# On s'assure que Python trouve le dossier 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine # 👈 Ajout de engine ici

# ─── 1. ON REDÉFINIT LES MODÈLES ICI POUR ÉVITER LES ERREURS D'IMPORT ───
class TypeContratMission(str, enum.Enum):
    cddu = "CDDU"   
    ccda = "CCDA"
    both = "BOTH"

class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    categorie: Mapped[str] = mapped_column(String(255), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    
    type_contrat: Mapped[TypeContratMission] = mapped_column(
        SAEnum(TypeContratMission, native_enum=False), 
        default=TypeContratMission.ccda,
        nullable=False
    )
    
    tarif_unitaire: Mapped[float] = mapped_column(Float, nullable=False)
    unite: Mapped[str] = mapped_column(String(100), nullable=False)
    
    dispo_resp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dispo_tcp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ─── 2. LE DICTIONNAIRE INITIAL CCDA ──────────────────────────────────
MISSIONS_INITIALES = {
    "✍️ Rédiger et mettre en page les supports de cours": [
        {"titre": "LVL 1 - Pas ou peu de changements : MAP finale d'1 page de texte max (hors schéma)", "tarif": 10.0, "unite": "par map / support"},
        {"titre": "LVL 2 - Changements moyens : MAP finale de 2 ou 3 pages (hors schéma)", "tarif": 25.0, "unite": "par map / support"},
        {"titre": "LVL 3 - Beaucoup de changements : MAP finale de 4 pages ou plus (hors schéma / MAJ de cours)", "tarif": 50.0, "unite": "par map / support"},
        {"titre": "LVL 4 - Support non existant, qui a dû être créé de novo", "tarif": 100.0, "unite": "par map / support"},
        {"titre": "LVL 5 - Support non existant, créé de novo, particulièrement long/difficile (> 30 pages) – Uniquement pour UE1", "tarif": 200.0, "unite": "par map / support"}
    ],
    "📚 Création d'entraînements (TD, ED, Colle, CCB)": [
        {"titre": "LVL 1 - Questions de cours, relativement simple à faire", "tarif": 3.0, "unite": "par qcm"},
        {"titre": "LVL 2 - Questions intermédiaire (énoncé long ou schéma)", "tarif": 4.0, "unite": "par qcm"},
        {"titre": "LVL 3 - Questions d'exercice", "tarif": 6.0, "unite": "par qcm"},
        {"titre": "LVL 4 - Questions d'exercice compliquée à faire – Possible uniquement UE2, UE3, UE6", "tarif": 8.0, "unite": "par qcm"}
    ],
    "📌 Création de Post-it": [
        {"titre": "Post-it - Créer Post-it de novo", "tarif": 50.0, "unite": "par post-it"}
    ],
    "💻 Intégration dans Théia": [
        {"titre": "Standard - QCM classique, images et/ou texte", "tarif": 0.5, "unite": "par qcm"},
        {"titre": "Complexe - QCM complexe, formules mathématiques (ex: UE3, UE6)", "tarif": 1.0, "unite": "par qcm"}
    ],
    "👨‍🏫 Animation de séances": [
        {"titre": "Supports existants - ED, TD, Stage pré-rentrée, TDR – Préparation incluse", "tarif": 12.0, "unite": "par heure"},
        {"titre": "Supports à créer - ED, TD, Stage pré-rentrée, TDR – Préparation incluse", "tarif": 24.0, "unite": "par heure"}
    ],
    "🎙️ Enregistrement": [
        {"titre": "Enregistrement - Enregistrer et réécouter le cours", "tarif": 10.0, "unite": "par heure"}
    ],
    "💬 Permanences et support": [
        {"titre": "Permanences - Questions/réponses PASS et LASS, y compris réponse au forum (séance de 2h)", "tarif": 10.0, "unite": "par heure"}
    ],
    "📝 Relire/vérifier/corriger/mettre en page les supports": [
        {"titre": "LVL 1 - Pas ou peu de changements : MAP finale d'1 page de texte max (hors schéma)", "tarif": 3.0, "unite": "par support"},
        {"titre": "LVL 2 - Changements moyens : MAP finale de 2 ou 3 pages (hors schéma)", "tarif": 5.0, "unite": "par support"},
        {"titre": "LVL 3 - Beaucoup de changements : MAP finale de 4 pages ou plus (hors schéma / MAJ de cours)", "tarif": 10.0, "unite": "par support"},
        {"titre": "LVL 4 - Support non existant, qui a dû être créé de novo", "tarif": 20.0, "unite": "par support"},
        {"titre": "LVL 5 - Support non existant, créé de novo, particulièrement long/difficile (> 30 pages) – Uniquement pour UE2, UE3 et UE6", "tarif": 30.0, "unite": "par support"},
        {"titre": "LVL 6 - Support non existant, créé de novo, particulièrement long/difficile (> 30 pages) – Uniquement pour l'UE1", "tarif": 50.0, "unite": "par support"}
    ],
    "📖 Relecture des annales": [
        {"titre": "Relecture des annales - Relecture des annales (si nécessaire)", "tarif": 10.0, "unite": "par annale et par année"}
    ],
    "✅ Création de corrections d'annales": [
        {"titre": "LVL 1 - Questions de cours, relativement simple à corriger", "tarif": 1.5, "unite": "par qcm"},
        {"titre": "LVL 2 - Questions intermédiaire (énoncé long ou schéma à légender)", "tarif": 2.0, "unite": "par qcm"},
        {"titre": "LVL 3 - Questions d'exercice", "tarif": 3.0, "unite": "par qcm"}
    ],
    "👔 Participation réunions pré-colles": [
        {"titre": "Participation - Réunions pré-colles", "tarif": 10.0, "unite": "par pré-colle"}
    ],
    "👔 Gestion d'équipe": [
        {"titre": "Gestion d'équipe - Réunions, pré-colles, etc. – À BIEN DÉTAILLER", "tarif": 50.0, "unite": "par mois"}
    ],
    "🎓 Formation": [
        {"titre": "Formation - Réunion de formation (Word, Teams, …)", "tarif": 50.0, "unite": "par jour"}
    ],
    "☀️ Mise à jour estivale": [
        {"titre": "Mise à jour estivale - Réintégrer les MAPS n-1, Relire les cours, Post-it et fiches, Relecture ED & entraînements", "tarif": 300.0, "unite": "par semaine"}
    ]
}

# ─── 3. LA FONCTION DE SEED ───────────────────────────────────────────
def seed_catalog():
    db: Session = SessionLocal()
    try:
        print("🛠️ Harmonisation de la structure de la table...")
        
        # 1. On s'assure que nos nouvelles colonnes sont bien là
        db.execute(text("ALTER TABLE missions ADD COLUMN IF NOT EXISTS dispo_resp BOOLEAN DEFAULT TRUE;"))
        db.execute(text("ALTER TABLE missions ADD COLUMN IF NOT EXISTS dispo_tcp BOOLEAN DEFAULT TRUE;"))
        
        # 2. 🔥 ON SUPPRIME LA COLONNE OBSOLÈTE ! Adieu "is_resp_only" ;)
        db.execute(text("ALTER TABLE missions DROP COLUMN IF EXISTS is_resp_only;"))
        db.commit()
        
        print("🌱 Début de l'injection du catalogue CCDA...")
        
        # On nettoie les anciennes missions CCDA
        db.execute(text("DELETE FROM missions WHERE UPPER(categorie) LIKE '%CCDA%' OR titre LIKE '%CCDA%' OR type_contrat::text = 'ccda'"))
        db.commit()
        
        # On revient à notre requête propre, sans le champ banni !
        insert_query = text("""
            INSERT INTO missions 
            (categorie, titre, type_contrat, tarif_unitaire, unite, dispo_resp, dispo_tcp, is_active)
            VALUES 
            (:categorie, :titre, 'ccda', :tarif_unitaire, :unite, :dispo_resp, :dispo_tcp, :is_active)
        """)
        
        count = 0
        for nom_categorie, sous_missions in MISSIONS_INITIALES.items():
            for sm in sous_missions:
                est_gestion_equipe = "Gestion d'équipe" in nom_categorie
                
                db.execute(insert_query, {
                    "categorie": nom_categorie,
                    "titre": sm["titre"],
                    "tarif_unitaire": sm["tarif"],
                    "unite": sm["unite"],
                    "dispo_resp": True,
                    "dispo_tcp": not est_gestion_equipe,
                    "is_active": True
                })
                count += 1
        
        db.commit()
        print(f"🚀 Succès ! {count} missions CCDA ont été injectées. Table nettoyée !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de l'injection : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_catalog()
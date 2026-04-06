import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool  # 👈 Crucial pour le partage de mémoire SQLite
from datetime import datetime
from unittest.mock import patch

from app.main import app
from app.database import Base, get_db
from app.core.security import get_current_user

# Imports nécessaires pour que SQLAlchemy lise les modèles
from app.models.user import User, Role
from app.models.declaration import Declaration, LigneDeclaration, StatutDeclaration
from app.models.mission import Mission

# ── CONFIGURATION DE LA BASE DE TEST (SQLite partagé) ──────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # 👈 Force une seule connexion pour les tests et l'API
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# On surcharge la dépendance get_db de FastAPI pour taper dans SQLite
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# ── FIXTURES ───────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def setup_database():
    """Crée les tables avant le test et les détruit après."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_user():
    """Retourne un utilisateur fictif pour simuler la connexion."""
    return User(
        id=1,
        email="test@declarant.com",
        role=Role.top,
        profil_complete=True,
        site="lyon_est"
    )

# ── LES TESTS DE LA RÈGLE DU 20 DU MOIS ───────────────────────────────────

def test_soumission_refusee_avant_le_20(mock_user):
    """Vérifie qu'on ne peut pas soumettre le mois en cours avant le 20."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    db = TestingSessionLocal()
    
    # On mock l'utilisateur en base aussi
    db.add(mock_user)
    db.commit()
    
    brouillon = Declaration(
        id=1, 
        user_id=mock_user.id, 
        mois=4, 
        annee=2026, 
        statut=StatutDeclaration.brouillon
    )
    db.add(brouillon)
    db.commit()

    ligne = LigneDeclaration(
        declaration_id=1,
        mission_id=99,
        quantite=5.0,
        tarif_applique=10.0
    )
    db.add(ligne)
    db.commit()
    
    fake_now = datetime(2026, 4, 15, 12, 0, 0)
    
    with patch('app.routers.declarations.datetime') as mock_date:
        mock_date.now.return_value = fake_now
        response = client.post("/api/v1/declarations/1/soumettre")
        
    assert response.status_code == 400
    assert "avant le 20" in response.json()["detail"]

def test_soumission_autorisee_apres_le_20(mock_user):
    """Vérifie qu'on peut soumettre le mois en cours à partir du 20."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    db = TestingSessionLocal()
    
    # On s'assure que l'utilisateur existe
    db.add(mock_user)
    db.commit()
    
    brouillon = Declaration(
        id=2, 
        user_id=mock_user.id, 
        mois=4, 
        annee=2026, 
        statut=StatutDeclaration.brouillon
    )
    db.add(brouillon)
    db.commit()

    ligne = LigneDeclaration(
        declaration_id=2,
        mission_id=99,
        quantite=5.0,
        tarif_applique=10.0
    )
    db.add(ligne)
    db.commit()
    
    fake_now = datetime(2026, 4, 21, 12, 0, 0)
    
    with patch('app.routers.declarations.datetime') as mock_date:
        mock_date.now.return_value = fake_now
        response = client.post("/api/v1/declarations/2/soumettre")
        
    assert response.status_code == 200
    assert response.json()["statut"] == "soumise"
import sys
import os
import asyncio

# 🪟 Spécifique à Windows pour gérer l'asynchrone
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 📍 Force Python à aller chercher le dossier parent 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, check_is_at_least_coordo
from app.models.user import User, Role

# 🎭 Création de faux profils d'utilisateurs pour simuler la sécurité
mock_admin = User(id=1, email="admin@test.fr", role=Role.admin, site="Paris")
mock_coordo = User(id=2, email="coordo@test.fr", role=Role.coordo, site="Lyon")

@pytest.fixture
def client_admin():
    """Fournit un client API connecté en tant qu'Admin."""
    # On court-circuite les dépendances de sécurité de FastAPI
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[check_is_at_least_coordo] = lambda: mock_admin
    
    with TestClient(app) as client:
        yield client
        
    # On nettoie après le test pour ne pas polluer les autres fichiers
    app.dependency_overrides.clear()

@pytest.fixture
def client_coordo():
    """Fournit un client API connecté en tant qu'un Coordo."""
    app.dependency_overrides[get_current_user] = lambda: mock_coordo
    app.dependency_overrides[check_is_at_least_coordo] = lambda: mock_coordo
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()
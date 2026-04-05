# backend/test/test_auth.py

import pytest
from httpx import AsyncClient, ASGITransport
from app.database import get_db
from app.main import app

# 1️⃣ Simulation d'une session de DB pour éviter le freeze PostgreSQL
class MockDB:
    def query(self, *args, **kwargs):
        return self
    
    def filter(self, *args, **kwargs):
        return self
        
    def first(self):
        # On simule un utilisateur trouvé en base !
        class FakeUser:
            id = 1
            email = "test@avicenne.fr"
            # On met un mot de passe haché bidon (adapte si ton router vérifie le hash)
            hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

            # 💡 On simule l'Enum attendu par ton router auth
            class role:
                value = "admin"
                
        return FakeUser()

# Fonction pour remplacer le get_db de FastAPI
async def override_get_db():
    try:
        yield MockDB()
    finally:
        pass


# 2️⃣ Tes tests modifiés
@pytest.mark.asyncio
async def test_login_success():
    # 💡 L'ASTUCE : On force FastAPI à utiliser notre faux MockDB au lieu du vrai !
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", data={
            "username": "test@avicenne.fr",
            "password": "secret"
        })
    
    # On nettoie la surcharge après le test pour ne pas polluer les autres fichiers
    app.dependency_overrides.clear()
    
    # On vérifie que l'API nous répond un succès (200 OK)
    assert response.status_code == 200
    # On vérifie qu'on récupère bien un token JWT
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password():
    # On remet la simulation
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", data={
            "username": "test@avicenne.fr",
            "password": "MauvaisPassword"
        })
    
    app.dependency_overrides.clear()
    
    # On s'attend à un refus (401 Unauthorized ou 400 Bad Request)
    assert response.status_code in [400, 401]
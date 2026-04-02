import pytest
from httpx import AsyncClient, ASGITransport
from app.core.security import get_current_user
from app.database import get_db
from app.main import app

# 1️⃣ Simulation d'un faux utilisateur connecté
async def mock_get_current_user():
    class FakeUser:
        id = 1
        email = "test@avicenne.fr"
        role = "admin"
        # 💡 On ajoute les champs types souvent obligatoires dans un modèle User
        nom = "Doe"
        prenom = "John"
        is_active = True
        nss_encrypted = None
        iban_encrypted = None
        profil_complete = True

    return FakeUser()

# 2️⃣ Simulation d'une session de DB pour éviter le freeze PostgreSQL
class MockDB:
    def query(self, *args, **kwargs): return self
    def filter(self, *args, **kwargs): return self
    def first(self):
        class FakeUser:
            id = 1
            email = "test@avicenne.fr"
            role = "admin"
        return FakeUser()

async def override_get_db():
    try:
        yield MockDB()
    finally:
        pass


# 3️⃣ Tes tests
@pytest.mark.asyncio
async def test_get_my_profile_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/users/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_profile_authenticated():
    # 💡 L'ASTUCE : On simule l'utilisateur ET la base de données
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/users/me")
    
    # On nettoie TOUTES les simulations après le test
    app.dependency_overrides.clear()
    
    # On s'attend à un succès
    assert response.status_code == 200
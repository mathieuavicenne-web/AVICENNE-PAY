# backend/app/main.py

from dotenv import load_dotenv
load_dotenv()
import os
import uuid
from fastapi import FastAPI, Request
import structlog
from app.core.logging_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, declarations, missions, paie, user 

# Récupération de la vériable d'env
origins_env = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://127.0.0.1:5173,http://10.10.12.75:5173"
)

# 1. Lancement de la configuration des logs
setup_logging()
logger = structlog.get_logger()

app = FastAPI(
    title="Avicenne Pay API",
    # 🛡️ 2. Déclaration du schéma de sécurité directement dans l'app
    swagger_ui_parameters={"persistAuthorization": True}, # Garde le token même si on actualise la page !
    openapi_components={
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    # Applique la sécurité BearerAuth à TOUTES les routes dans la doc Swagger
    security=[{"BearerAuth": []}] 
)

# 2. Middleware qui capture les requêtes
@app.middleware("http")
async def add_structured_logs(request: Request, call_next):
    # On crée un identifiant unique pour cette requête
    request_id = str(uuid.uuid4())
    
    # On lie cet ID au logger de cette requête précise
    log = logger.new(request_id=request_id, path=request.url.path, method=request.method)
    
    log.info("Requête reçue")
    
    try:
        response = await call_next(request)
        log.info("Requête traitée avec succès", status_code=response.status_code)
        return response
    except Exception as e:
        log.error("La requête a planté !", error=str(e))
        raise e


# transformation de la chaîne en une vraie liste Python ['URL1', 'URL2']
origins = [origin.strip() for origin in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"], # Autorise tous les headers
)

# 🚦 3. AJOUT DU ROUTEUR USERS
app.include_router(user.router) # 👈 Ajouté ici !
app.include_router(missions.router) 
app.include_router(auth.router)
app.include_router(declarations.router)
app.include_router(paie.router)

@app.get("/", tags=["Root"]) # Un petit tag pour faire joli dans Swagger
def read_root():
    return {"message": "Bienvenue sur l'API d'Avicenne Pay !"}

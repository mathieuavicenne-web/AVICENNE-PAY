# AVICENNE-PAY 💰

Application de gestion et de synthèse de paie pour les collaborateurs d'Avicenne.
**Backend :** FastAPI (Python) | **Frontend :** Vue.js 3 (Vite)

---

## 🏗️ Architecture du Projet

Le projet est découpé en deux parties principales (Monorepo) :

```text
AVICENNE-PAY/
├── backend/            # API REST - FastAPI
│   ├── app/
│   │   ├── core/       # Sécurité, JWT, configuration
│   │   ├── models/     # Modèles SQLAlchemy (Base de données)
│   │   ├── routers/    # Points d'accès API (Auth, Paie, etc.)
│   │   └── schemas/    # Modèles Pydantic (Validation des données)
│   └── requirements.txt# Dépendances Python
│
└── frontend/           # Interface Utilisateur - Vue.js 3
    ├── src/
    │   ├── components/ # Composants réutilisables
    │   ├── router/     # Gestion des routes (Vue Router)
    │   └── views/      # Pages de l'application (Login, Home...)
    └── package.json    # Dépendances Node.js

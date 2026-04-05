# AVICENNE-PAY 💰

Application de gestion et de synthèse de paie pour les collaborateurs d'Avicenne.
**Backend :** FastAPI (Python) | **Frontend :** Vue.js 3 (Vite)

---

## 🏗️ Architecture du Projet

Le projet est structuré en Monorepo :

```text
AVICENNE-PAY/
├── backend/                  # --- API REST (FastAPI) ---
│   ├── app/
│   │   ├── core/             # Sécurité, JWT, référentiels
│   │   ├── models/           # Modèles de la Base de données (SQLAlchemy)
│   │   ├── routers/          # Points d'entrée de l'API (Auth, Paie, Users...)
│   │   ├── schemas/          # Modèles de validation des données (Pydantic)
│   │   └── main.py           # Fichier d'entrée de l'application
│   ├── tests/                # Tests automatisés (Pytest)
│   ├── .env                  # Variables d'environnement
│   └── requirements.txt      # Dépendances Python
│
└── frontend/                 # --- Interface Utilisateur (Vue.js 3) ---
    ├── public/               # Fichiers statiques
    ├── src/
    │   ├── assets/           # CSS et images
    │   ├── components/       # Composants Vue réutilisables
    │   ├── router/           # Gestion des routes UI (Vue Router)
    │   ├── services/         # Appels API (Axios, etc.)
    │   └── views/            # Pages (Login, Dashboard, Profil, Users...)
    ├── package.json          # Dépendances Node.js
    └── tailwind.config.js    # Configuration du design CSS
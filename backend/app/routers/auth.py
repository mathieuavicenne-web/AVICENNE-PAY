# backend/app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import verify_password, create_access_token, get_password_hash, create_refresh_token, SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter(
    prefix="/auth",
    tags=["Authentification"]
)

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. On vérifie si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )
    
    # 2. On extrait les données du schéma en dictionnaire (sans le mot de passe)
    user_data = user_in.model_dump(exclude={"password"})
    
    # 3. On hache le mot de passe
    hashed_password = get_password_hash(user_in.password)
    
    # 4. On crée l'utilisateur avec TOUS les champs d'un coup ! ✨
    new_user = User(
        **user_data,
        hashed_password=hashed_password,
        is_active=True
    )
    
    # 5. On l'enregistre en base de données
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 🔑 On génère les DEUX tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)}) # 👈 Nouveau
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Vérifie le refresh token et génère un nouvel access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. On décode le refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # 2. Sécurité : On vérifie que c'est bien un token de type 'refresh'
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception

    # 3. On récupère l'utilisateur
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # 4. On génère un NOUVEL access token
    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
# backend/routers/missions.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Role, User
from app.models.mission import Mission, TypeContratMission
from app.schemas.mission import MissionCreate, MissionUpdate, MissionResponse 
from app.core.security import get_current_user, check_is_at_least_coordo

router = APIRouter(prefix="/missions", tags=["Missions"])

# 🔓 LECTURE : Filtrée selon le rôle
@router.get("/", response_model=List[MissionResponse])
def get_missions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # On récupère TOUT (actives et inactives)
    query = db.query(Mission) 
    
    # On garde le filtrage par rôle (sécurité métier)
    if current_user.role != Role.admin:
        if current_user.role == Role.resp:
            query = query.filter(Mission.dispo_resp == True)
        elif current_user.role == Role.tcp:
            query = query.filter(Mission.dispo_tcp == True)
        
    return query.order_by(Mission.is_active.desc(), Mission.categorie.asc()).all()

# 🔒 CRÉATION : Réservée aux Admins (Tout) et Coordos (Uniquement CCDA)
@router.post("/", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(
    mission_in: MissionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) 
):
    # 🛡️ Blindage avec .value pour éviter les conflits d'Enum
    if current_user.role == Role.coordo and mission_in.type_contrat != TypeContratMission.ccda.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="En tant que Coordinateur, vous ne pouvez créer que des missions de type CCDA."
        )
        
    new_mission = Mission(**mission_in.model_dump())
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    return new_mission


# 🔒 MODIFICATION / TOGGLE : Réservée aux Admins (Tout) et Coordos (Uniquement CCDA)
@router.put("/{mission_id}", response_model=MissionResponse)
def update_mission(
    mission_id: int,
    mission_in: MissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) 
):
    db_mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission introuvable.")
        
    if current_user.role == Role.coordo:
        # 🛡️ Blindage .value ici aussi
        if db_mission.type_contrat != TypeContratMission.ccda.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="En tant que Coordinateur, vous ne pouvez pas modifier une mission qui n'est pas CCDA."
            )
            
        # 🛡️ Et ici aussi !
        if mission_in.type_contrat and mission_in.type_contrat != TypeContratMission.ccda.value:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez pas basculer une mission CCDA vers un autre type de contrat."
            )
        
    update_data = mission_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mission, key, value)
        
    db.commit()
    db.refresh(db_mission)
    return db_mission


# 🔒 SUPPRESSION VIRTUELLE : Réservée aux Admins (Tout) et Coordos (Uniquement CCDA)
@router.delete("/{mission_id}", response_model=MissionResponse)
def delete_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) 
):
    db_mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission introuvable.")
        
    # 🛡️ Blindage .value final
    if current_user.role == Role.coordo and db_mission.type_contrat != TypeContratMission.ccda.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="En tant que Coordinateur, vous ne pouvez désactiver que des missions de type CCDA."
        )
        
    db_mission.is_active = False
    
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.delete("/{mission_id}/definitive")
def delete_mission_definitive(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) 
):
    db_mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission introuvable.")
        
    db.delete(db_mission) # 💥 Suppression réelle
    db.commit()
    return {"message": "Mission supprimée définitivement"}
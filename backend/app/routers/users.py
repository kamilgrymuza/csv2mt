from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import verify_token

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/me", response_model=schemas.User)
async def read_current_user(current_user: models.User = Depends(verify_token)):
    return current_user


@router.put("/me", response_model=schemas.User)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return crud.update_user(db=db, user_id=current_user.id, user=user_update)


@router.get("/", response_model=List[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_token)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users
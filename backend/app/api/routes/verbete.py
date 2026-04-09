from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.models.log import LogAction
from app.schemas.verbete import VerbeteCreate, VerbeteUpdate, VerbeteOut
from app.services import verbete_service
from app.services.log_service import log_action
from app.utils.pagination import paginate

router = APIRouter(prefix="/admin/verbetes", tags=["admin-verbetes"])


@router.post("", response_model=VerbeteOut, status_code=status.HTTP_201_CREATED)
def create_verbete(
    payload: VerbeteCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    verbete = verbete_service.create_verbete(db, payload)
    log_action(db, LogAction.create, admin.id, "verbete", verbete.id, f"Criado: {verbete.term}")
    return verbete


@router.get("")
def list_verbetes(
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=100),
    letter: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    items, total = verbete_service.list_verbetes(
        db, page=page, page_size=page_size,
        public_only=False, letter=letter
    )
    return paginate(items, total, page, page_size)


@router.get("/{verbete_id}", response_model=VerbeteOut)
def get_verbete(
    verbete_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    verbete = verbete_service.get_verbete_by_id(db, verbete_id)
    if not verbete:
        raise HTTPException(status_code=404, detail="Verbete não encontrado.")
    return verbete


@router.put("/{verbete_id}", response_model=VerbeteOut)
def update_verbete(
    verbete_id: int,
    payload: VerbeteUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    verbete = verbete_service.update_verbete(db, verbete_id, payload)
    if not verbete:
        raise HTTPException(status_code=404, detail="Verbete não encontrado.")
    log_action(db, LogAction.update, admin.id, "verbete", verbete_id, f"Editado: {verbete.term}")
    return verbete


@router.delete("/{verbete_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_verbete(
    verbete_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    verbete = verbete_service.soft_delete_verbete(db, verbete_id)
    if not verbete:
        raise HTTPException(status_code=404, detail="Verbete não encontrado.")
    log_action(db, LogAction.delete, admin.id, "verbete", verbete_id, "Soft delete")


@router.patch("/{verbete_id}/feature", response_model=VerbeteOut)
def feature_verbete(
    verbete_id: int,
    featured: bool = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    verbete = verbete_service.toggle_featured_verbete(db, verbete_id, featured)
    if not verbete:
        raise HTTPException(status_code=404, detail="Verbete não encontrado.")
    action = LogAction.feature if featured else LogAction.unfeature
    log_action(db, action, admin.id, "verbete", verbete_id)
    return verbete

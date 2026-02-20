from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import escrow
from app import models
from ..database import get_db
from .deps import get_current_user

router = APIRouter()

@router.post("/create", response_model=escrow.Escrow)
def create_escrow(
    *,
    db: Session = Depends(get_db),
    escrow_in: escrow.EscrowCreate,
    current_user: models.models.User = Depends(get_current_user),
) -> Any:
    seller = db.query(models.models.User).filter(models.models.User.email == escrow_in.seller_email).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    escrow_obj = models.models.Escrow(
        title=escrow_in.title,
        description=escrow_in.description,
        amount=escrow_in.amount,
        buyer_id=current_user.id,
        seller_id=seller.id,
    )
    db.add(escrow_obj)
    db.commit()
    db.refresh(escrow_obj)
    
    for milestone_in in escrow_in.milestones:
        milestone_obj = models.models.Milestone(
            **milestone_in.dict(),
            escrow_id=escrow_obj.id
        )
        db.add(milestone_obj)
    
    db.commit()
    db.refresh(escrow_obj)
    return escrow_obj

@router.get("/user/all", response_model=List[escrow.Escrow])
def get_user_escrows(
    db: Session = Depends(get_db),
    current_user: models.models.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    escrows = db.query(models.models.Escrow).filter(
        (models.models.Escrow.buyer_id == current_user.id) | 
        (models.models.Escrow.seller_id == current_user.id)
    ).offset(skip).limit(limit).all()
    return escrows

@router.get("/dashboard", response_model=escrow.DashboardData)
def get_dashboard_data(
    current_user: models.models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    active_escrows = db.query(models.models.Escrow).filter(
        ((models.models.Escrow.buyer_id == current_user.id) | (models.models.Escrow.seller_id == current_user.id)) &
        (models.models.Escrow.status != models.models.EscrowStatus.COMPLETED) &
        (models.models.Escrow.status != models.models.EscrowStatus.CANCELLED)
    ).count()

    completed_escrows = db.query(models.models.Escrow).filter(
        ((models.models.Escrow.buyer_id == current_user.id) | (models.models.Escrow.seller_id == current_user.id)) &
        (models.models.Escrow.status == models.models.EscrowStatus.COMPLETED)
    ).count()

    pending_milestones = db.query(models.models.Milestone).join(models.models.Escrow).filter(
        (models.models.Escrow.seller_id == current_user.id) &
        (models.models.Milestone.is_completed == False)
    ).count()

    return {
        "balance": current_user.balance,
        "active_escrows_count": active_escrows,
        "completed_escrows_count": completed_escrows,
        "pending_milestones_count": pending_milestones
    }

@router.get("/{id}", response_model=escrow.Escrow)
def get_escrow(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.models.User = Depends(get_current_user),
) -> Any:
    escrow = db.query(models.models.Escrow).filter(models.models.Escrow.id == id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    if escrow.buyer_id != current_user.id and escrow.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return escrow

@router.post("/{id}/fund")
def fund_escrow(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.models.User = Depends(get_current_user),
) -> Any:
    escrow = db.query(models.models.Escrow).filter(models.models.Escrow.id == id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    if escrow.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only buyer can fund the escrow")
    if escrow.status != models.models.EscrowStatus.PENDING:
        raise HTTPException(status_code=400, detail="Escrow is already funded or closed")
    
    if current_user.balance < escrow.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    current_user.balance -= escrow.amount
    escrow.status = models.models.EscrowStatus.FUNDED
    db.commit()
    return {"message": "Escrow funded successfully"}

@router.post("/{id}/release")
def release_escrow(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.models.User = Depends(get_current_user),
) -> Any:
    escrow = db.query(models.models.Escrow).filter(models.models.Escrow.id == id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    if escrow.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only buyer can release the funds")
    if escrow.status != models.models.EscrowStatus.FUNDED:
        raise HTTPException(status_code=400, detail="Escrow must be funded to release funds")
    
    seller = db.query(models.models.User).filter(models.models.User.id == escrow.seller_id).first()
    seller.balance += escrow.amount
    escrow.status = models.models.EscrowStatus.COMPLETED
    for milestone in escrow.milestones:
        milestone.is_completed = True
    
    db.commit()
    return {"message": "Funds released successfully"}

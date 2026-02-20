from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float

class MilestoneCreate(MilestoneBase):
    pass

class Milestone(MilestoneBase):
    id: int
    is_completed: bool
    escrow_id: int

    class Config:
        from_attributes = True

class EscrowBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float

class EscrowCreate(EscrowBase):
    seller_email: str
    milestones: List[MilestoneCreate] = []

class EscrowUpdate(BaseModel):
    status: Optional[str] = None

class Escrow(EscrowBase):
    id: int
    status: str
    buyer_id: int
    seller_id: int
    created_at: datetime
    updated_at: datetime
    milestones: List[Milestone] = []

    class Config:
        from_attributes = True

class DashboardData(BaseModel):
    balance: float
    active_escrows_count: int
    completed_escrows_count: int
    pending_milestones_count: int

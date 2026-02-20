from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    escrows_as_buyer = relationship("Escrow", back_populates="buyer", foreign_keys="Escrow.buyer_id")
    escrows_as_seller = relationship("Escrow", back_populates="seller", foreign_keys="Escrow.seller_id")

class EscrowStatus:
    PENDING = "pending"
    FUNDED = "funded"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"

class Escrow(Base):
    __tablename__ = "escrows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    amount = Column(Float, nullable=False)
    status = Column(String, default=EscrowStatus.PENDING)
    
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="escrows_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="escrows_as_seller")
    milestones = relationship("Milestone", back_populates="escrow")

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    amount = Column(Float)
    is_completed = Column(Boolean, default=False)
    
    escrow_id = Column(Integer, ForeignKey("escrows.id"))
    escrow = relationship("Escrow", back_populates="milestones")

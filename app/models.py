from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .database import Base


class RequestStatus(enum.Enum):
    new = "new"
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)

    assigned_requests = relationship("ServiceRequest", back_populates="master",
                                     foreign_keys="ServiceRequest.assigned_to")


class ServiceRequest(Base):  # ← Важно: ServiceRequest, не Request
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    problem_text = Column(String, nullable=False)
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.new, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    version = Column(Integer, default=1, nullable=False)

    master = relationship("User", back_populates="assigned_requests", foreign_keys=[assigned_to])
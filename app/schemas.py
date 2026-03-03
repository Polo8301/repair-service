from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


# ENUM для статусов (дублируем для Pydantic)
class RequestStatus(str, Enum):
    new = "new"
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


# Схема для создания заявки (входные данные)
class ServiceRequestCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100, description="Имя клиента")
    phone: str = Field(..., min_length=10, max_length=20, description="Телефон")
    address: str = Field(..., min_length=5, max_length=200, description="Адрес")
    problem_text: str = Field(..., min_length=10, max_length=1000, description="Описание проблемы")


# Схема заявки для ответа (полные данные из БД)
class ServiceRequestResponse(BaseModel):
    id: int
    client_name: str
    phone: str
    address: str
    problem_text: str
    status: RequestStatus
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    version: int

    model_config = ConfigDict(from_attributes=True)


# Схема для обновления статуса заявки
class ServiceRequestStatusUpdate(BaseModel):
    status: RequestStatus
    version: int  # для оптимистичной блокировки


# Схема пользователя (для выбора при входе)
class UserSelect(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


# Схема для назначения мастера
class AssignMasterRequest(BaseModel):
    assigned_to: int
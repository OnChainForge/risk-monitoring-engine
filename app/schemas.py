from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    field: str
    operator: str
    threshold: Optional[float] = None
    threshold_json: Optional[Any] = None
    severity: str = "medium"
    is_active: bool = True


class RuleOut(RuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class EventCreate(BaseModel):
    source: str
    payload: dict


class EventOut(EventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    received_at: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rule_id: int
    event_id: int
    severity: str
    message: str
    triggered_at: datetime
    resolved: bool

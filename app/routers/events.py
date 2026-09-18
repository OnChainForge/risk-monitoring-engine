from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.rules_engine import evaluate_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=list[schemas.AlertOut])
def ingest_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    alerts = evaluate_event(db, db_event)
    return alerts

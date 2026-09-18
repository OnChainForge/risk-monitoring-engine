from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[schemas.AlertOut])
def list_alerts(
    resolved: bool | None = Query(default=None),
    severity: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """List alerts, optionally filtered by resolved status and/or severity."""
    query = db.query(models.Alert)
    if resolved is not None:
        query = query.filter(models.Alert.resolved == resolved)
    if severity:
        query = query.filter(models.Alert.severity == severity)
    return query.order_by(models.Alert.triggered_at.desc()).all()


@router.patch("/{alert_id}/resolve", response_model=schemas.AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as resolved."""
    alert = db.get(models.Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert

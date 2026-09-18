from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/", response_model=schemas.RuleOut)
def create_rule(rule: schemas.RuleCreate, db: Session = Depends(get_db)):
    """Create a new rule. Fails if a rule with the same name already exists."""
    existing = db.query(models.Rule).filter(models.Rule.name == rule.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="A rule with this name already exists")
    db_rule = models.Rule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.get("/", response_model=list[schemas.RuleOut])
def list_rules(db: Session = Depends(get_db)):
    """List all rules, newest first."""
    return db.query(models.Rule).order_by(models.Rule.id.desc()).all()


@router.patch("/{rule_id}/toggle", response_model=schemas.RuleOut)
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    """Enable or disable a rule."""
    rule = db.get(models.Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a rule permanently."""
    rule = db.get(models.Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"detail": "Rule deleted"}

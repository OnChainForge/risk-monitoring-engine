import logging
from typing import Any
from sqlalchemy.orm import Session

from app.models import Rule, Event, Alert

logger = logging.getLogger("rules_engine")

OPERATORS = {
    ">": lambda v, t: v > t,
    "<": lambda v, t: v < t,
    ">=": lambda v, t: v >= t,
    "<=": lambda v, t: v <= t,
    "==": lambda v, t: v == t,
    "!=": lambda v, t: v != t,
    "in": lambda v, t: v in t,
    "not_in": lambda v, t: v not in t,
}


def _extract_value(payload: dict, field: str) -> Any:
    """Supports simple dot-notation paths like 'a.b.c'."""
    value = payload
    for part in field.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def evaluate_event(db: Session, event: Event) -> list[Alert]:
    """Evaluates an event against all active rules and generates alerts."""
    triggered_alerts = []
    active_rules = db.query(Rule).filter(Rule.is_active.is_(True)).all()

    for rule in active_rules:
        try:
            value = _extract_value(event.payload, rule.field)
            if value is None:
                continue

            op_func = OPERATORS.get(rule.operator)
            if op_func is None:
                logger.warning(f"Unknown operator in rule {rule.id}: {rule.operator}")
                continue

            threshold = rule.threshold_json if rule.threshold_json is not None else rule.threshold
            if op_func(value, threshold):
                alert = Alert(
                    rule_id=rule.id,
                    event_id=event.id,
                    severity=rule.severity,
                    message=(
                        f"Rule '{rule.name}' triggered: field '{rule.field}' "
                        f"= {value} {rule.operator} {threshold}"
                    ),
                )
                db.add(alert)
                triggered_alerts.append(alert)
                logger.info(f"ALERT generated: {alert.message}")

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id} on event {event.id}: {e}")
            continue

    if triggered_alerts:
        db.commit()
        for a in triggered_alerts:
            db.refresh(a)

    return triggered_alerts
def evaluate_payload(db: Session, payload: dict) -> dict:
    """
    Evaluates a raw payload against all active rules WITHOUT persisting
    an Event. Returns a risk score (0-100) and a plain-language explanation.
    Used for on-demand analysis (e.g. /analyze/{tx_hash}), as opposed to
    evaluate_event(), which is used for the streaming/event-ingestion flow.
    """
    active_rules = db.query(Rule).filter(Rule.is_active.is_(True)).all()

    triggered = []
    severity_weight = {"low": 10, "medium": 25, "high": 40, "critical": 60}

    for rule in active_rules:
        try:
            value = _extract_value(payload, rule.field)
            if value is None:
                continue

            op_func = OPERATORS.get(rule.operator)
            if op_func is None:
                continue

            threshold = rule.threshold_json if rule.threshold_json is not None else rule.threshold
            if op_func(value, threshold):
                triggered.append({
                    "rule": rule.name,
                    "severity": rule.severity,
                    "reason": f"field '{rule.field}' = {value} {rule.operator} {threshold}",
                })

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id} on payload: {e}")
            continue

    score = min(100, sum(severity_weight.get(t["severity"], 10) for t in triggered))

    if score == 0:
        risk_level = "low"
        explanation = "No rules were triggered. This transaction shows no known risk patterns."
    elif score < 40:
        risk_level = "low"
        explanation = f"{len(triggered)} minor rule(s) triggered. Overall risk is low."
    elif score < 70:
        risk_level = "medium"
        explanation = f"{len(triggered)} rule(s) triggered, including moderate risk signals."
    else:
        risk_level = "high"
        explanation = f"{len(triggered)} rule(s) triggered, indicating significant risk signals."

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "explanation": explanation,
        "triggered_rules": triggered,
    }

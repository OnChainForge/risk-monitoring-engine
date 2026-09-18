import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.blockchain import fetch_transaction
from app.rules_engine import evaluate_payload

logger = logging.getLogger("analyze")

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/{tx_hash}")
def analyze_transaction(tx_hash: str, db: Session = Depends(get_db)):
    """
    Fetches a transaction from Ethereum by its hash, normalizes it,
    evaluates it against all active rules, and returns a risk score
    with an explanation. Read-only: does not persist anything.
    """
    try:
        payload = fetch_transaction(tx_hash)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch transaction {tx_hash}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch transaction from the RPC provider")

    result = evaluate_payload(db, payload)

    return {
        "tx_hash": tx_hash,
        "transaction": payload,
        **result,
    }

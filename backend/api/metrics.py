"""Metrics endpoints.

Expose rolling statistics for an account such as total trading days, number
of profitable days, consistency percentage and drawdown.  Uses the
``risk_engine`` service to compute values.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .deps import get_current_account
from ..db import models
from ..db.session import get_db
from ..services.risk_engine import compute_consistency, eligible_profit

router = APIRouter()


@router.get("/{account_id}")
def get_metrics(
    account_id: str,
    account: models.Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Return current metrics for the requested account.

    Note: only the owner of the account can query its metrics.
    """
    if account.id != account_id:
        return {"detail": "Access denied"}
    total_days, profitable_days, consistency_pct = compute_consistency(account.id, db)
    gain_value, gain_pct = eligible_profit(account, db)
    return {
        "total_trading_days": total_days,
        "profitable_days": profitable_days,
        "consistency_pct": consistency_pct,
        "profit_gain": round(gain_value, 2),
        "profit_gain_pct": round(gain_pct, 2),
    }

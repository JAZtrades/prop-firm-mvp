"""Account endpoints for traders.

Currently only exposes ``/accounts/me`` which returns the balance,
peak equity, trailing drawdown percentage and eligibility flags.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .deps import get_current_user, get_current_account
from ..db import models
from ..db.session import get_db
from ..services.risk_engine import compute_consistency, update_equity_and_drawdown, eligible_profit, check_payout_eligibility

router = APIRouter()


@router.get("/me")
def get_my_account(
    account: models.Account = Depends(get_current_account), db: Session = Depends(get_db)
):
    """Return a snapshot of the current account including metrics and flags."""
    # Compute trailing drawdown based on stored values
    current_balance = float(account.current_balance)
    peak_equity = float(account.peak_equity)
    drawdown_pct = (
        (peak_equity - current_balance) / peak_equity * 100 if peak_equity > 0 else 0
    )

    # Compute consistency and eligibility on the fly
    total_days, profitable_days, consistency_pct = compute_consistency(account.id, db)
    gain_value, gain_pct = eligible_profit(account, db)
    eligible, eligible_amount = check_payout_eligibility(account, db)

    return {
        "account_id": account.id,
        "balance": current_balance,
        "peak_equity": peak_equity,
        "trailing_drawdown_pct": round(drawdown_pct, 2),
        "consistency_pct": consistency_pct,
        "total_trading_days": total_days,
        "profitable_days": profitable_days,
        "profit_gain": round(gain_value, 2),
        "profit_gain_pct": round(gain_pct, 2),
        "eligible_for_payout": eligible,
        "eligible_amount": round(float(eligible_amount), 2) if eligible else 0,
    }

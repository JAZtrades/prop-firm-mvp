"""Payout request endpoints for traders.

Allows traders to request a payout if eligibility gates are satisfied.  The
request will be queued and later approved by an admin or automatically
settled by the worker.
"""
import random
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, condecimal
from sqlalchemy.orm import Session

from .deps import get_current_account
from ..db import models
from ..db.session import get_db
from ..services.risk_engine import check_payout_eligibility, capped_payout_amount, eligible_profit

router = APIRouter()


class PayoutRequestIn(BaseModel):
    requested_amount: float


@router.get("/")
def list_payouts(
    account: models.Account = Depends(get_current_account), db: Session = Depends(get_db)
):
    """List payout requests for the current account."""
    payouts = (
        db.query(models.PayoutRequest)
        .filter(models.PayoutRequest.account_id == account.id)
        .order_by(models.PayoutRequest.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "requested_amount": float(p.requested_amount),
            "eligible_amount_at_request": float(p.eligible_amount_at_request),
            "status": p.status.value,
            "settlement_eta": p.settlement_eta,
            "created_at": p.created_at,
        }
        for p in payouts
    ]


@router.post("/request", status_code=status.HTTP_201_CREATED)
def request_payout(
    request: PayoutRequestIn,
    account: models.Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Create a payout request if the account meets all eligibility criteria."""
    eligible, eligible_amount = check_payout_eligibility(account, db)
    if not eligible:
        raise HTTPException(
            status_code=400, detail="Account not eligible for payout"
        )
    # Cap requested amount according to probation days
    capped_amount = capped_payout_amount(account, request.requested_amount, db)
    if capped_amount <= 0:
        raise HTTPException(status_code=400, detail="Requested amount exceeds eligible profit")
    # Determine settlement ETA within configured range (7–14 days) from Config
    cfg = db.query(models.Config).first()
    if cfg is None:
        # create default config row if missing
        cfg = models.Config()
        db.add(cfg)
        db.flush()
    min_days = int(cfg.settlement_days_min)
    max_days = int(cfg.settlement_days_max)
    settle_days = random.randint(min_days, max_days)
    settlement_eta = date.today() + timedelta(days=settle_days)
    payout = models.PayoutRequest(
        account_id=account.id,
        requested_amount=capped_amount,
        eligible_amount_at_request=eligible_amount,
        status=models.PayoutStatus.queued,
        settlement_eta=settlement_eta,
    )
    db.add(payout)
    db.commit()
    return {
        "payout_id": payout.id,
        "requested_amount": float(payout.requested_amount),
        "settlement_eta": payout.settlement_eta,
        "status": payout.status.value,
    }

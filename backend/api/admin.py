"""Admin endpoints for reviewing payout requests and managing accounts.

These endpoints require the current user to have the ``admin`` role.  For
simplicity the role check is done inline; in a production application you
would create a reusable dependency.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .deps import get_current_user
from ..db import models
from ..db.session import get_db

router = APIRouter()


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


@router.get("/payouts/queue")
def list_payout_queue(
    db: Session = Depends(get_db), admin: models.User = Depends(require_admin)
):
    """Return payout requests in queued state awaiting approval."""
    requests = (
        db.query(models.PayoutRequest)
        .filter(models.PayoutRequest.status == models.PayoutStatus.queued)
        .order_by(models.PayoutRequest.created_at.asc())
        .all()
    )
    return [
        {
            "id": p.id,
            "account_id": p.account_id,
            "requested_amount": float(p.requested_amount),
            "eligible_amount_at_request": float(p.eligible_amount_at_request),
            "settlement_eta": p.settlement_eta,
        }
        for p in requests
    ]


class ApprovalIn(BaseModel):
    payout_id: str


@router.post("/payouts/approve")
def approve_payout(
    approval: ApprovalIn,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Approve a queued payout request and set status to approved."""
    payout = db.query(models.PayoutRequest).get(approval.payout_id)
    if payout is None:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.status != models.PayoutStatus.queued:
        raise HTTPException(status_code=400, detail="Payout not in queue")
    payout.status = models.PayoutStatus.approved
    db.commit()
    return {"message": "approved"}


class RejectIn(BaseModel):
    payout_id: str
    reason: str


@router.post("/payouts/reject")
def reject_payout(
    rejection: RejectIn,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Reject a payout request with a note."""
    payout = db.query(models.PayoutRequest).get(rejection.payout_id)
    if payout is None:
        raise HTTPException(status_code=404, detail="Payout not found")
    payout.status = models.PayoutStatus.rejected
    payout.notes = rejection.reason
    db.commit()
    return {"message": "rejected"}


class SuspendIn(BaseModel):
    account_id: str


@router.post("/accounts/suspend")
def suspend_account(
    suspend: SuspendIn,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Suspend an account immediately.

    This sets the account status to ``suspended``.
    """
    account = db.query(models.Account).get(suspend.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account.status = models.AccountStatus.suspended
    db.commit()
    return {"message": f"account {account.id} suspended"}

"""Endpoints for ingesting and listing trades.

Trades drive the state of an account: balances, peak equity and drawdown.
When a batch of trades is ingested the account is updated and daily
statistics are recorded.
"""
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .deps import get_current_account
from ..db import models
from ..db.session import get_db
from ..services.risk_engine import (
    update_equity_and_drawdown,
)

router = APIRouter()


class TradeIn(BaseModel):
    trade_date: date
    pnl: float
    instrument: str = ""
    qty: int = 0
    meta: dict = {}


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_trades(
    trades: List[TradeIn],
    account: models.Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Ingest a list of trades and update account metrics."""
    total_pnl = 0.0
    # Add trades to the database
    for trade_in in trades:
        trade = models.Trade(
            account_id=account.id,
            trade_date=trade_in.trade_date,
            pnl=trade_in.pnl,
            instrument=trade_in.instrument,
            qty=trade_in.qty,
            meta=trade_in.meta,
        )
        db.add(trade)
        total_pnl += trade_in.pnl
    db.flush()

    # Update account balance and peak equity
    new_balance = float(account.current_balance) + total_pnl
    account.current_balance = new_balance
    if new_balance > float(account.peak_equity):
        account.peak_equity = new_balance
    db.flush()

    # Record daily stats
    # Group trades by date to compute daily PnL
    pnl_by_date = {}
    for t in trades:
        pnl_by_date.setdefault(t.trade_date, 0.0)
        pnl_by_date[t.trade_date] += t.pnl

    for trade_date, pnl in pnl_by_date.items():
        ds = (
            db.query(models.DailyStats)
            .filter(
                models.DailyStats.account_id == account.id,
                models.DailyStats.date == trade_date,
            )
            .first()
        )
        if ds is None:
            ds = models.DailyStats(
                account_id=account.id,
                date=trade_date,
                day_realized_pnl=pnl,
                closed_equity=new_balance,
                is_profitable_day=pnl > 0,
            )
            db.add(ds)
        else:
            ds.day_realized_pnl = float(ds.day_realized_pnl) + pnl
            ds.closed_equity = new_balance
            ds.is_profitable_day = ds.day_realized_pnl > 0
        db.flush()

    # Recompute trailing drawdown and suspend if necessary
    update_equity_and_drawdown(account, float(account.current_balance), db)
    db.commit()
    return {"trades_ingested": len(trades), "new_balance": float(account.current_balance)}

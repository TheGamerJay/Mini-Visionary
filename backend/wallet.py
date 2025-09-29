# wallet.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import select

from models import get_session, User, CreditLedger, CreditEventType

def grant_credits(
    user_id: int,
    amount: int,
    event: CreditEventType = CreditEventType.GRANT,
    ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> bool:
    """
    Add credits to user's balance and log to CreditLedger.
    Use event=PURCHASE for store purchases, event=GRANT for bonuses, etc.
    """
    if amount <= 0:
        return False

    with get_session() as s:
        # Lock the row to avoid race conditions
        stmt = select(User).where(User.id == user_id).with_for_update()
        user = s.execute(stmt).scalar_one_or_none()
        if not user:
            return False

        user.credits = (user.credits or 0) + amount

        s.add(CreditLedger(
            user_id=user.id,
            event=event,
            amount=amount,   # positive for grants/purchases
            ref=ref,
            notes=notes,
            created_at=datetime.utcnow()
        ))
        s.commit()
        return True


def spend_credits(
    user_id: int,
    amount: int,
    ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> bool:
    """
    Deduct credits and log as SPEND. Returns False if insufficient balance.
    """
    if amount <= 0:
        return False

    with get_session() as s:
        stmt = select(User).where(User.id == user_id).with_for_update()
        user = s.execute(stmt).scalar_one_or_none()
        if not user:
            return False

        current = user.credits or 0
        if current < amount:
            return False

        user.credits = current - amount
        s.add(CreditLedger(
            user_id=user.id,
            event=CreditEventType.SPEND,
            amount=-amount,  # negative for spend
            ref=ref,
            notes=notes,
            created_at=datetime.utcnow()
        ))
        s.commit()
        return True


def refund_credits(
    user_id: int,
    amount: int,
    ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> bool:
    """
    Refund (add back) credits and log as REFUND.
    """
    if amount <= 0:
        return False

    with get_session() as s:
        stmt = select(User).where(User.id == user_id).with_for_update()
        user = s.execute(stmt).scalar_one_or_none()
        if not user:
            return False

        user.credits = (user.credits or 0) + amount
        s.add(CreditLedger(
            user_id=user.id,
            event=CreditEventType.REFUND,
            amount=amount,  # positive
            ref=ref,
            notes=notes,
            created_at=datetime.utcnow()
        ))
        s.commit()
        return True


def get_credits(user_id: int) -> int:
    with get_session() as s:
        user = s.get(User, user_id)
        return int(user.credits or 0) if user else 0

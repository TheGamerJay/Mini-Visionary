from models import get_session, User

def spend_credits(user_id: int, amount: int) -> bool:
    """Spend credits from user's wallet. Returns True if successful, False if insufficient credits."""
    with get_session() as s:
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            return False

        current_credits = user.credits or 0
        if current_credits < amount:
            return False

        user.credits = current_credits - amount
        s.commit()
        return True

def get_credits(user_id: int) -> int:
    """Get current credit balance for user."""
    with get_session() as s:
        user = s.query(User).filter_by(id=user_id).first()
        return user.credits if user else 0
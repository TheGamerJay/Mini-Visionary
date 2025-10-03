#!/usr/bin/env python3
"""Clear all library entries for specific user."""
import os
import sys
from sqlalchemy import create_engine, text

def clear_library():
    """Clear library table for user."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        sys.exit(1)

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Get user ID for dagamerjay13@gmail.com
        result = conn.execute(text("""
            SELECT id FROM users WHERE email = 'dagamerjay13@gmail.com'
        """))
        user = result.first()

        if not user:
            sys.exit(1)

        user_id = user[0]

        # Delete all library entries for this user
        result = conn.execute(text("""
            DELETE FROM library WHERE user_id = :user_id
        """), {"user_id": user_id})

        conn.commit()

if __name__ == "__main__":
    clear_library()

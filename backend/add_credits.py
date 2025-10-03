#!/usr/bin/env python3
"""Add credits to user."""
import os
import sys
from sqlalchemy import create_engine, text

def add_credits():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        sys.exit(1)

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Add 100 credits to dagamerjay13@gmail.com
        conn.execute(text("""
            UPDATE users
            SET credits = credits + 100
            WHERE email = 'dagamerjay13@gmail.com'
        """))

        conn.commit()

if __name__ == "__main__":
    add_credits()

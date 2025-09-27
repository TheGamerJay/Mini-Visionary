#!/usr/bin/env python3
"""
Quick database cleanup script for production.
Removes gambling/betting columns and adds Mini Visionary columns.
"""

import os
from sqlalchemy import create_engine, text

# Production cleanup queries
CLEANUP_SQL = """
-- Remove gambling/betting related columns
ALTER TABLE users DROP COLUMN IF EXISTS balance;
ALTER TABLE users DROP COLUMN IF EXISTS referral_code;
ALTER TABLE users DROP COLUMN IF EXISTS username;
ALTER TABLE users DROP COLUMN IF EXISTS is_admin;
ALTER TABLE users DROP COLUMN IF EXISTS last_login;

-- Add Mini Visionary specific columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ad_free BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);

-- Drop gambling tables if they exist
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS bets CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS game_sessions CASCADE;
DROP TABLE IF EXISTS withdrawals CASCADE;
DROP TABLE IF EXISTS deposits CASCADE;
"""

def run_cleanup():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        return

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Execute each statement separately
        statements = [s.strip() for s in CLEANUP_SQL.split(';') if s.strip()]

        for stmt in statements:
            if stmt.startswith('--') or not stmt:
                continue
            try:
                print(f"Executing: {stmt[:50]}...")
                conn.execute(text(stmt))
                conn.commit()
                print("✅ Success")
            except Exception as e:
                print(f"⚠️ Warning: {e}")

    print("🎉 Database cleanup completed!")

if __name__ == "__main__":
    run_cleanup()
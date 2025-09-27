#!/usr/bin/env python3
"""Database migration script to add missing columns for existing databases."""

import sqlite3
import os
from models import get_engine

def main():
    print(">> Running database migration...")

    # Get the database file path
    database_url = os.getenv("DATABASE_URL", "sqlite:///./mini_visionary.db")
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
    else:
        print("ERROR: This migration script only supports SQLite databases")
        return

    if not os.path.exists(db_path):
        print(f"ERROR: Database file {db_path} does not exist")
        return

    print(f">> Migrating database: {db_path}")

    # Connect directly to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if tables exist first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f">> Existing tables: {tables}")

        # Create all missing tables using init_db
        from models import init_db
        init_db()
        print(">> Ensured all tables exist")

        # Migrate users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f">> Current user table columns: {columns}")

        # Add missing columns to users table
        missing_columns = []

        if 'ad_free' not in columns:
            missing_columns.append(('ad_free', 'BOOLEAN DEFAULT 0'))

        if 'stripe_customer_id' not in columns:
            missing_columns.append(('stripe_customer_id', 'VARCHAR(255)'))

        if 'display_name' not in columns:
            missing_columns.append(('display_name', 'VARCHAR(100)'))

        if 'avatar_url' not in columns:
            missing_columns.append(('avatar_url', 'VARCHAR(500)'))

        if 'is_active' not in columns:
            missing_columns.append(('is_active', 'BOOLEAN DEFAULT 1'))

        if 'created_at' not in columns:
            missing_columns.append(('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'))

        if 'updated_at' not in columns:
            missing_columns.append(('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'))

        # Add missing columns to users
        for column_name, column_def in missing_columns:
            print(f">> Adding users column: {column_name}")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")

        # Migrate poster_jobs table if it exists
        if 'poster_jobs' in tables:
            cursor.execute("PRAGMA table_info(poster_jobs)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f">> Current poster_jobs table columns: {columns}")

            if 'progress' not in columns:
                print(">> Adding poster_jobs column: progress")
                cursor.execute("ALTER TABLE poster_jobs ADD COLUMN progress INTEGER DEFAULT 0")

            if 'error_message' not in columns:
                print(">> Adding poster_jobs column: error_message")
                cursor.execute("ALTER TABLE poster_jobs ADD COLUMN error_message VARCHAR(1000)")

        conn.commit()

        if missing_columns:
            print(f">> Added {len(missing_columns)} missing columns to users table")
        else:
            print(">> No missing columns found in users table")

        # Verify the structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f">> Updated user table columns: {columns}")

        if 'poster_jobs' in tables:
            cursor.execute("PRAGMA table_info(poster_jobs)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f">> Updated poster_jobs table columns: {columns}")

        print(">> Migration completed successfully")

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Migrate avatar_url column from VARCHAR(500) to TEXT to support data URLs
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    exit(1)

def migrate():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if using SQLite
        if 'sqlite' in DATABASE_URL:
            print("Detected SQLite database")
            print("Migrating avatar_url column to TEXT type...")

            # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
            # Step 1: Create new table with correct schema
            conn.execute(text("""
                CREATE TABLE users_new (
                    id INTEGER NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255),
                    display_name VARCHAR(100),
                    avatar_url TEXT,
                    credits INTEGER NOT NULL,
                    ad_free BOOLEAN DEFAULT 0,
                    stripe_customer_id VARCHAR(255),
                    is_active BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    PRIMARY KEY (id),
                    UNIQUE (email)
                )
            """))

            # Step 2: Copy data from old table
            conn.execute(text("""
                INSERT INTO users_new (id, email, password_hash, display_name, avatar_url,
                                       credits, ad_free, stripe_customer_id, is_active,
                                       created_at, updated_at)
                SELECT id, email, password_hash, display_name, avatar_url,
                       credits, ad_free, stripe_customer_id, is_active,
                       created_at, updated_at
                FROM users
            """))

            # Step 3: Drop old table
            conn.execute(text("DROP TABLE users"))

            # Step 4: Rename new table
            conn.execute(text("ALTER TABLE users_new RENAME TO users"))

            conn.commit()
            print("Migration complete - avatar_url is now TEXT type")
            print("Please restart the Flask app for changes to take effect")
            return

        # PostgreSQL migration
        # Check current column type
        result = conn.execute(text("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'avatar_url'
        """))

        current = result.fetchone()
        if current:
            print(f"Current avatar_url type: {current[0]} ({current[1]})")

        # Alter column to TEXT
        print("Changing avatar_url to TEXT type...")
        conn.execute(text("ALTER TABLE users ALTER COLUMN avatar_url TYPE TEXT"))
        conn.commit()

        print("✅ Successfully migrated avatar_url column to TEXT")

        # Verify
        result = conn.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'avatar_url'
        """))
        new_type = result.fetchone()
        print(f"New avatar_url type: {new_type[0]}")

if __name__ == "__main__":
    migrate()
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
                    avatar_image_url TEXT,
                    avatar_video_url TEXT,
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

            # Step 2: Copy data from old table (avatar_url becomes avatar_image_url)
            conn.execute(text("""
                INSERT INTO users_new (id, email, password_hash, display_name, avatar_image_url,
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
            print("Migration complete - split avatar_url into avatar_image_url and avatar_video_url")
            print("Please restart the Flask app for changes to take effect")
            return

        # PostgreSQL migration
        print("PostgreSQL detected - migrating columns...")

        # Add new columns
        conn.execute(text("ALTER TABLE users ADD COLUMN avatar_image_url TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN avatar_video_url TEXT"))

        # Copy existing avatar_url data to avatar_image_url
        conn.execute(text("UPDATE users SET avatar_image_url = avatar_url WHERE avatar_url IS NOT NULL"))

        # Drop old column
        conn.execute(text("ALTER TABLE users DROP COLUMN avatar_url"))

        conn.commit()
        print("Migration complete - split avatar_url into avatar_image_url and avatar_video_url")
        print("Please restart the Flask app for changes to take effect")

if __name__ == "__main__":
    migrate()
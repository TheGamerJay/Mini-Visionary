#!/usr/bin/env python3
"""Create library table in production database."""
import os
import sys
from sqlalchemy import create_engine, text

def create_library_table():
    """Create the library table if it doesn't exist."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        sys.exit(1)

    # Fix postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if library table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'library'
            );
        """))
        exists = result.scalar()

        if exists:
            return

        # Create library table
        conn.execute(text("""
            CREATE TABLE library (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                image_job_id INTEGER NOT NULL REFERENCES image_jobs(id) ON DELETE CASCADE,
                collection_name VARCHAR(64) NOT NULL DEFAULT 'mini_library',
                notes TEXT,
                is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))

        # Create indexes
        conn.execute(text("""
            CREATE INDEX ix_library_user_id ON library(user_id);
        """))

        conn.execute(text("""
            CREATE INDEX ix_library_image_job_id ON library(image_job_id);
        """))

        conn.execute(text("""
            CREATE INDEX ix_library_user_collection ON library(user_id, collection_name);
        """))

        conn.commit()

if __name__ == "__main__":
    create_library_table()

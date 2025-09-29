#!/usr/bin/env python3
"""
Add display_name column to users table
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'display_name'
            """))

            if result.fetchone():
                print("display_name column already exists, nothing to do")
                return

            # Add the column
            print("Adding display_name column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
            conn.commit()
            print("✅ Successfully added display_name column")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
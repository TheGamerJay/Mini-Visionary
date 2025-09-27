#!/usr/bin/env python3
"""Initialize the database with all required tables."""

import os
import sys
from models import init_db, get_session, User, Poster, PosterJob, Asset, CreditLedger

def main():
    print(">> Initializing database...")

    try:
        # Initialize all tables
        init_db()
        print(">> Database tables created successfully")

        # Test database connection and basic operations
        with get_session() as session:
            # Check if tables exist by querying them
            user_count = session.query(User).count()
            poster_count = session.query(Poster).count()
            job_count = session.query(PosterJob).count()
            asset_count = session.query(Asset).count()
            credit_count = session.query(CreditLedger).count()

            print(f">> Database stats:")
            print(f"   Users: {user_count}")
            print(f"   Posters: {poster_count}")
            print(f"   Jobs: {job_count}")
            print(f"   Assets: {asset_count}")
            print(f"   Credit transactions: {credit_count}")

        print(">> Database is ready and working!")

    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
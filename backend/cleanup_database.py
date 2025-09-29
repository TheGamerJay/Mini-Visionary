#!/usr/bin/env python3
"""
Database cleanup script to remove gambling/betting related columns and tables.
This will clean up the database to match the Mini Visionary poster generation app.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def cleanup_database():
    """Remove gambling/betting related columns and tables from the database."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            print("🧹 Starting database cleanup...")

            # Start transaction
            trans = conn.begin()

            try:
                # Remove gambling/betting related columns from users table
                cleanup_queries = [
                    # Remove balance column (gambling related)
                    "ALTER TABLE users DROP COLUMN IF EXISTS balance",

                    # Remove referral_code column (not needed for poster app)
                    "ALTER TABLE users DROP COLUMN IF EXISTS referral_code",

                    # Remove username column (we're using display_name instead)
                    "ALTER TABLE users DROP COLUMN IF EXISTS username",

                    # Remove admin flag (not needed for current app)
                    "ALTER TABLE users DROP COLUMN IF EXISTS is_admin",

                    # Remove last_login tracking (not needed)
                    "ALTER TABLE users DROP COLUMN IF EXISTS last_login",
                ]

                # Add missing columns that should exist for Mini Visionary
                add_columns = [
                    # Add credits for poster generation (if not exists)
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 0",

                    # Add ad_free flag (if not exists)
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS ad_free BOOLEAN DEFAULT FALSE",

                    # Add stripe customer ID for payments (if not exists)
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)",

                    # Add avatar URL for user profiles (if not exists)
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255)",
                ]

                # Execute cleanup queries
                for query in cleanup_queries:
                    try:
                        print(f"🔧 Executing: {query}")
                        conn.execute(text(query))
                        print("✅ Success")
                    except Exception as e:
                        print(f"⚠️  Warning: {e}")
                        # Continue with other queries even if one fails

                # Execute add column queries
                for query in add_columns:
                    try:
                        print(f"🔧 Executing: {query}")
                        conn.execute(text(query))
                        print("✅ Success")
                    except Exception as e:
                        print(f"⚠️  Warning: {e}")

                # Drop gambling/betting related tables if they exist
                gambling_tables = [
                    "DROP TABLE IF EXISTS games CASCADE",
                    "DROP TABLE IF EXISTS bets CASCADE",
                    "DROP TABLE IF EXISTS transactions CASCADE",
                    "DROP TABLE IF EXISTS game_sessions CASCADE",
                    "DROP TABLE IF EXISTS withdrawals CASCADE",
                    "DROP TABLE IF EXISTS deposits CASCADE",
                ]

                for query in gambling_tables:
                    try:
                        print(f"🗑️  Executing: {query}")
                        conn.execute(text(query))
                        print("✅ Success")
                    except Exception as e:
                        print(f"⚠️  Warning: {e}")

                # Commit all changes
                trans.commit()
                print("✅ Database cleanup completed successfully!")
                print("🎨 Your database is now clean and ready for Mini Visionary poster generation!")

                return True

            except Exception as e:
                trans.rollback()
                print(f"❌ Error during cleanup: {e}")
                return False

    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to run the cleanup."""
    print("🧹 Mini Visionary Database Cleanup Tool")
    print("=" * 50)
    print("This will remove gambling/betting related columns and tables.")
    print("⚠️  Make sure you have a database backup before proceeding!")

    # Ask for confirmation
    confirm = input("\nDo you want to proceed with the cleanup? (yes/no): ").lower().strip()

    if confirm not in ['yes', 'y']:
        print("❌ Cleanup cancelled.")
        return

    # Run cleanup
    success = cleanup_database()

    if success:
        print("\n🎉 Cleanup completed successfully!")
        print("📝 Your database structure is now aligned with Mini Visionary.")
    else:
        print("\n❌ Cleanup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
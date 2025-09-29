#!/usr/bin/env python3
"""Fix credits directly in production PostgreSQL database"""

import psycopg2
import sys

def fix_production_credits():
    # Connect directly to production PostgreSQL using public URL
    conn_string = "postgresql://postgres:PtznVvouCSknyrDHjGYqRYwHjDteLqRZ@maglev.proxy.rlwy.net:22676/railway"

    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # First, check what tables exist
        print("Checking tables...")
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        print(f"Tables found: {[t[0] for t in tables]}")

        # Check if we have users table
        if ('users',) in tables:
            table_name = 'users'
        elif ('user',) in tables:
            table_name = '"user"'
        else:
            print("No users table found!")
            return False

        print(f"Using table: {table_name}")

        # Check current user data
        cursor.execute(f"SELECT id, email, credits FROM {table_name} WHERE id = 6;")
        user = cursor.fetchone()

        if user:
            print(f"Found user ID 6: email={user[1]}, credits={user[2]}")

            # Update credits to 20
            cursor.execute(f"UPDATE {table_name} SET credits = 20 WHERE id = 6;")
            conn.commit()

            # Verify the update
            cursor.execute(f"SELECT id, email, credits FROM {table_name} WHERE id = 6;")
            updated_user = cursor.fetchone()
            print(f"Updated user ID 6: email={updated_user[1]}, credits={updated_user[2]}")

            print("✅ Credits fixed successfully!")
            return True
        else:
            print("User ID 6 not found!")

            # Show all users
            cursor.execute(f"SELECT id, email, credits FROM {table_name};")
            all_users = cursor.fetchall()
            print("All users:")
            for u in all_users:
                print(f"  ID: {u[0]}, Email: {u[1]}, Credits: {u[2]}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = fix_production_credits()
    if not success:
        sys.exit(1)
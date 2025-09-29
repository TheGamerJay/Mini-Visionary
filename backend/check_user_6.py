#!/usr/bin/env python3
"""Check user ID 6 specifically"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def check_user_6():
    with get_session() as s:
        user = s.query(User).filter_by(id=6).first()
        if user:
            print(f"User ID 6 found:")
            print(f"Email: {user.email}")
            print(f"Display Name: {user.display_name}")
            print(f"Credits: {user.credits}")
        else:
            print("User ID 6 not found")
            # Show all users to see what IDs exist
            all_users = s.query(User).all()
            print(f"\nAll users in database:")
            for u in all_users:
                print(f"ID: {u.id}, Email: {u.email}, Credits: {u.credits}")

if __name__ == "__main__":
    check_user_6()
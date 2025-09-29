#!/usr/bin/env python3
"""List all users in the database"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def list_users():
    with get_session() as s:
        users = s.query(User).all()
        if not users:
            print("No users found in database!")
            return

        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Display Name: {user.display_name}")
            print(f"Credits: {user.credits}")
            print("-" * 30)

if __name__ == "__main__":
    list_users()
#!/usr/bin/env python3
"""Delete jaaye@test.com user"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def delete_jaaye_user():
    with get_session() as s:
        user = s.query(User).filter_by(email="jaaye@test.com").first()
        if not user:
            print("User jaaye@test.com not found!")
            return False

        print(f"Deleting user: {user.email} (ID: {user.id})")
        s.delete(user)
        s.commit()
        print("User deleted successfully!")
        return True

if __name__ == "__main__":
    success = delete_jaaye_user()
    if not success:
        print("Failed to delete user!")
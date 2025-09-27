#!/usr/bin/env python3
"""Fix user credits to 20"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def fix_user_credits(email, new_credits):
    with get_session() as s:
        user = s.query(User).filter_by(email=email.lower().strip()).first()
        if not user:
            print(f"User {email} not found!")
            return False

        old_credits = user.credits
        user.credits = new_credits
        s.commit()

        print(f"Credits updated for {user.email} (ID: {user.id})")
        print(f"Old credits: {old_credits}")
        print(f"New credits: {new_credits}")
        return True

if __name__ == "__main__":
    # Fix credits for the user
    success = fix_user_credits("acelenene@gmail.com", 20)
    if success:
        print("✅ Credits fixed successfully!")
    else:
        print("❌ Failed to fix credits!")
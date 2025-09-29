#!/usr/bin/env python3
"""Fix credits for user ID 6 (aceelnene@gmail.com) directly"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def fix_user_6_credits():
    with get_session() as s:
        user = s.query(User).filter_by(id=6).first()
        if not user:
            print("User ID 6 not found!")
            return False

        old_credits = user.credits
        user.credits = 20
        s.commit()

        print(f"Credits updated for {user.email} (ID: {user.id})")
        print(f"Old credits: {old_credits}")
        print(f"New credits: 20")
        return True

if __name__ == "__main__":
    success = fix_user_6_credits()
    if success:
        print("Credits fixed successfully!")
    else:
        print("Failed to fix credits!")
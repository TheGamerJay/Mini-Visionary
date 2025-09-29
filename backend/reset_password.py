#!/usr/bin/env python3
"""Reset password for a user"""

import os
import sys
sys.path.append('.')

from models import get_session, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def reset_user_password(email, new_password):
    with get_session() as s:
        user = s.query(User).filter_by(email=email.lower().strip()).first()
        if not user:
            print(f"User {email} not found!")
            return False

        # Hash the new password
        hashed = bcrypt.generate_password_hash(new_password).decode()
        user.password_hash = hashed
        s.commit()

        print(f"Password reset successfully for {user.email} (ID: {user.id})")
        return True

if __name__ == "__main__":
    # Reset password for the user
    success = reset_user_password("aceelnene@gmail.com", "Yariel@13")
    if success:
        print("✅ Password reset complete!")
        print("You can now login with:")
        print("Email: aceelnene@gmail.com")
        print("Password: Yariel@13")
    else:
        print("❌ Password reset failed!")
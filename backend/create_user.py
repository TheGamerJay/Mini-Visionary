#!/usr/bin/env python3
"""Create a user account for testing"""

import os
import sys
sys.path.append('.')

from models import get_session, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_user_account(display_name, email, password):
    with get_session() as s:
        # Check if user exists
        existing = s.query(User).filter_by(email=email.lower().strip()).first()
        if existing:
            print(f"User {email} already exists!")
            return existing

        # Create new user
        hashed = bcrypt.generate_password_hash(password).decode()
        user = User(
            display_name=display_name,
            email=email.lower().strip(),
            password_hash=hashed,
            credits=20
        )
        s.add(user)
        s.commit()
        s.refresh(user)
        print(f"Created user: {user.email} with ID: {user.id}")
        return user

if __name__ == "__main__":
    # Create account for the real user
    user = create_user_account("Jaaye", "aceelnene@gmail.com", "Yariel@13")
    print(f"User created successfully!")
    print(f"Email: {user.email}")
    print(f"Password: Yariel@13")
    print(f"Credits: {user.credits}")
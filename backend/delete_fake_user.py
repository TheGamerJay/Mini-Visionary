#!/usr/bin/env python3
"""Delete fake aceelnene@gmail.com user from wrong database"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def delete_fake_user():
    with get_session() as s:
        user = s.query(User).filter_by(email="aceelnene@gmail.com").first()
        if not user:
            print("User aceelnene@gmail.com not found!")
            return False

        print(f"Deleting fake user: {user.email} (ID: {user.id})")
        s.delete(user)
        s.commit()
        print("Fake user deleted successfully!")
        return True

if __name__ == "__main__":
    success = delete_fake_user()
    if not success:
        print("Failed to delete fake user!")
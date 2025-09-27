#!/usr/bin/env python3
"""Check acelenene@gmail.com specifically"""

import os
import sys
sys.path.append('.')

from models import get_session, User

def check_acelenene():
    with get_session() as s:
        user = s.query(User).filter_by(email="acelenene@gmail.com").first()
        if user:
            print(f"Found user: acelenene@gmail.com")
            print(f"ID: {user.id}")
            print(f"Display Name: {user.display_name}")
            print(f"Credits: {user.credits}")
        else:
            print("acelenene@gmail.com not found")

if __name__ == "__main__":
    check_acelenene()
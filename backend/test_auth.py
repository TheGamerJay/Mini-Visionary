#!/usr/bin/env python3
"""Test authentication endpoints directly"""

import requests
import json

BASE_URL = "https://minivisionary.soulbridgeai.com"

def test_signup():
    """Test signup endpoint"""
    url = f"{BASE_URL}/api/auth/signup"
    data = {
        "display_name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }

    print(f">> Testing signup: {url}")
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f">> Status: {response.status_code}")
        print(f">> Headers: {dict(response.headers)}")

        if response.headers.get('content-type', '').startswith('application/json'):
            print(f">> Response: {response.json()}")
        else:
            print(f">> Response text: {response.text[:500]}")

        return response
    except Exception as e:
        print(f">> Error: {e}")
        return None

def test_login():
    """Test login endpoint"""
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password123"
    }

    print(f">> Testing login: {url}")
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f">> Status: {response.status_code}")
        print(f">> Headers: {dict(response.headers)}")

        if response.headers.get('content-type', '').startswith('application/json'):
            print(f">> Response: {response.json()}")
        else:
            print(f">> Response text: {response.text[:500]}")

        return response
    except Exception as e:
        print(f">> Error: {e}")
        return None

def test_health():
    """Test health endpoint"""
    url = f"{BASE_URL}/api/health"

    print(f">> Testing health: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f">> Status: {response.status_code}")
        print(f">> Response: {response.json()}")
        return response
    except Exception as e:
        print(f">> Error: {e}")
        return None

if __name__ == "__main__":
    print(">> Testing authentication endpoints...")

    # Test health first
    test_health()
    print()

    # Test signup
    test_signup()
    print()

    # Test login
    test_login()
    print()

    print(">> Tests completed")
#!/usr/bin/env python3
"""
Script to create initial user account
Usage: python create_initial_user.py
"""

import os
import sys


# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uuid
from datetime import datetime

import bcrypt

from db.database import SessionLocal
from db.models import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_initial_user():
    """Create the initial user - credentials should be provided via environment variables"""

    import os

    # Get credentials from environment or prompt
    email = os.getenv("INITIAL_USER_EMAIL")
    password = os.getenv("INITIAL_USER_PASSWORD")
    first_name = os.getenv("INITIAL_USER_FIRST_NAME", "Admin")
    last_name = os.getenv("INITIAL_USER_LAST_NAME", "User")

    if not email or not password:
        print("Error: INITIAL_USER_EMAIL and INITIAL_USER_PASSWORD environment variables must be set")
        print(
            "Example: INITIAL_USER_EMAIL=admin@example.com INITIAL_USER_PASSWORD=your_secure_password python create_initial_user.py"
        )
        return

    # Create database session
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists (ID: {existing_user.id})")
            return

        # Hash the password
        password_hash = hash_password(password)

        # Create the user
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )

        # Add to database
        db.add(user)
        db.commit()
        db.refresh(user)

        print("✓ Initial user created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print("  Password: secret (hashed)")
        print(f"  Active: {user.is_active}")
        print(f"  Created: {user.created_at}")

    except Exception as e:
        print(f"✗ Error creating user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating initial user account...")
    create_initial_user()

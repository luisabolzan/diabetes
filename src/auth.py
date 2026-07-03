import hashlib
import os
import uuid
from src.database import SessionLocal, User

def login_user(email_or_username: str, password: str) -> tuple[bool, str, dict]:
    """
    Log in a user via SQLite Local DB.
    Returns: (Success, Message, SessionData)
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()

        if not user:
            return False, "Invalid email/username or password.", {}

        # Recompute hash
        pwd_hash = hashlib.sha256((password + user.salt).encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            return False, "Invalid email/username or password.", {}

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "access_token": str(uuid.uuid4()),
            "refresh_token": str(uuid.uuid4())
        }
        return True, "Login Successful", user_data

    except Exception as e:
        return False, f"Login Failed: {str(e)}", {}
    finally:
        db.close()

def register_user(email: str, password: str, metadata: dict = None) -> tuple[bool, str]:
    """
    Register a new user via SQLite Local DB.
    Returns: (Success, Message)
    """
    if not email or not password:
        return False, "Email and password are required."

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == email)
        ).first()
        if existing_user:
            return False, "User already exists with this email or username."

        salt = os.urandom(32).hex()
        pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        username = email.split('@')[0] if '@' in email else email
        
        # Verify username unique
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            username = f"{username}_{uuid.uuid4().hex[:6]}"

        new_user = User(
            username=username,
            email=email,
            password_hash=pwd_hash,
            salt=salt
        )
        db.add(new_user)
        db.commit()
        
        return True, "Registration successful!"

    except Exception as e:
        return False, f"Registration Failed: {str(e)}"
    finally:
        db.close()

def logout_user():
    """Sign out the current user (noop locally, NiceGUI clears storage)."""
    pass

def reset_password_email(email: str) -> tuple[bool, str]:
    """Send a mock password reset email."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.email == email) | (User.username == email)
        ).first()
        if not user:
            return False, "User not found."
            
        return True, f"Password reset link sent to {user.email} (simulated)."
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        db.close()


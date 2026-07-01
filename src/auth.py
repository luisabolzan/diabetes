import hashlib
import os
import uuid
from src.database import SessionLocal, User

def login_user(email: str, password: str) -> tuple[bool, str, dict]:
    """
    Log in a user via local SQLite database.
    Returns: (Success, Message, SessionData)
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            return False, "Login Failed: Invalid email or password.", {}

        # Verify password hash
        pwd_hash = hashlib.sha256((password + user.salt).encode('utf-8')).hexdigest()
        if pwd_hash != user.password_hash:
            return False, "Login Failed: Invalid email or password.", {}

        # Mock session data for compatibility
        user_data = {
            "id": user.id,
            "email": user.email,
            "access_token": f"mock_token_{uuid.uuid4().hex}",
            "refresh_token": f"mock_refresh_{uuid.uuid4().hex}"
        }
        return True, "Login Successful", user_data

    except Exception as e:
        return False, f"Login Error: {str(e)}", {}
    finally:
        session.close()

def register_user(email: str, password: str, metadata: dict = None) -> tuple[bool, str]:
    """
    Register a new user via local SQLite database.
    Returns: (Success, Message)
    """
    session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            return False, "Registration Failed: Email already registered."

        # Create new user with hashed password
        salt = os.urandom(32).hex()
        pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        # Use email prefix as username if not provided
        username = email.split('@')[0]
        
        new_user = User(
            username=username,
            email=email,
            password_hash=pwd_hash,
            salt=salt
        )
        session.add(new_user)
        session.commit()
        
        return True, "Registration successful! You can now log in."

    except Exception as e:
        session.rollback()
        return False, f"Registration Error: {str(e)}"
    finally:
        session.close()

def logout_user():
    """Sign out the current user (mocked)."""
    # UI handles clearing storage; nothing needed here for local SQLite session
    pass

def reset_password_email(email: str) -> tuple[bool, str]:
    """Mock sending a password reset email."""
    # Logic is mocked to avoid network requests [Errno -2]
    print(f"DEBUG: Password reset requested for: {email}")
    print("DEBUG: Email logic is currently MOCKED. No real email sent.")
    
    # In a real app, we'd check if the user exists first, 
    # but for this DNS fix, we just return success.
    return True, "Mock: Password reset instructions printed to console (DNS Error bypass active)."

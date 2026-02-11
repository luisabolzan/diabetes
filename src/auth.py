from src.config import supabase

def login_user(email: str, password: str) -> tuple[bool, str, dict]:
    """
    Log in a user via Supabase.
    Returns: (Success, Message, SessionData)
    """
    if not supabase:
        return False, "Supabase client not initialized.", {}

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        # Supabase returns a Session object if successful
        session = response.session
        user = response.user
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "access_token": session.access_token,
            "refresh_token": session.refresh_token
        }
        return True, "Login Successful", user_data

    except Exception as e:
        # e.message is common in Supabase errors, but fallback to str(e)
        msg = getattr(e, "message", str(e))
        return False, f"Login Failed: {msg}", {}

def register_user(email: str, password: str, metadata: dict = None) -> tuple[bool, str]:
    """
    Register a new user via Supabase.
    Returns: (Success, Message)
    """
    if not supabase:
        return False, "Supabase client not initialized."

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata or {}
            }
        })
        
        # Check if email confirmation is required
        if response.user and not response.session:
             return True, "Registration successful! Please check your email to confirm your account."
        elif response.user and response.session:
             return True, "Registration successful! You are logged in."
        else:
             return False, "Registration failed (Unknown error)."

    except Exception as e:
        msg = getattr(e, "message", str(e))
        return False, f"Registration Failed: {msg}"

def logout_user():
    """Sign out the current user."""
    if supabase:
        supabase.auth.sign_out()

def reset_password_email(email: str) -> tuple[bool, str]:
    """Send a password reset email."""
    if not supabase:
        return False, "Supabase client not initialized."
        
    try:
        supabase.auth.reset_password_email(email)
        return True, "Password reset email sent."
    except Exception as e:
        msg = getattr(e, "message", str(e))
        return False, f"Error: {msg}"

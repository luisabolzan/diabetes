import os
from supabase import create_client, Client

# Credentials from mobile-ios-pwa/.env.local
# Ideally these should be in a .env file, but for now we hardcode defaults
# based on the user's project structure to ensure it works out of the box.
_DEFAULT_URL = "https://zxrontqiwlmcauuzlnkk.supabase.co"
_DEFAULT_KEY = "sb_publishable_ogrTzrXv6FdEkfXTGYN3Kg_125AevmM"

SUPABASE_URL = os.environ.get("SUPABASE_URL", _DEFAULT_URL)
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", _DEFAULT_KEY)

# Initialize Supabase Client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Failed to initialize Supabase: {e}")
    supabase = None

import socket
import requests
SUPABASE_URL = "https://zxrontqiwlmcauuzlnkk.supabase.co"


print(f"Testing URL: {SUPABASE_URL}")

hostname = SUPABASE_URL.replace("https://", "").replace("http://", "").split("/")[0]
print(f"hostname: {hostname}")

try:
    info = socket.getaddrinfo(hostname, 443)
    print(f"DNS Resolution: Success -> {info[0][4]}")
except Exception as e:
    print(f"DNS Resolution: FAILED -> {e}")

try:
    print("Attempting HTTP GET...")
    r = requests.get(SUPABASE_URL, timeout=5)
    print(f"HTTP Status: {r.status_code}")
except Exception as e:
    print(f"HTTP Connection: FAILED -> {e}")

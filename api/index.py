from nicegui import app
import sys
import os

# Add src to path if needed, though usually standard in Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

# Import main to register the UI pages and components
# This executes the code in main.py but skips ui.run() because of the __name__ guard
import main

# Vercel looks for 'app'
# We don't need to call ui.run() here because we are being served by Vercel's ASGI wrapper

from src.database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    print("Checking for 'weight' column in 'settings' table...")
    with engine.connect() as conn:
        try:
            # Check if column exists by trying to select it
            conn.execute(text("SELECT weight FROM settings LIMIT 1"))
            print("'weight' column already exists.")
        except Exception:
            print("Column not found. Adding 'weight' column...")
            conn.execute(text("ALTER TABLE settings ADD COLUMN weight FLOAT DEFAULT 70.0"))
            print("Column added successfully.")
            
if __name__ == "__main__":
    migrate()

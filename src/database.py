from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

# Define the base
Base = declarative_base()

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    icr_breakfast = Column(Float, default=10.0)
    icr_lunch = Column(Float, default=15.0)
    icr_dinner = Column(Float, default=20.0)
    icr_snack = Column(Float, default=15.0)
    isf = Column(Float, default=50.0) # Insulin Sensitivity Factor
    target_glucose = Column(Integer, default=90) # Target Blood Glucose
    correction_threshold = Column(Integer, default=120) # Threshold for correction


    # Dynamic Modifiers (Activity)
    mod_gym = Column(Float, default=0.10)
    mod_run = Column(Float, default=-0.30)
    mod_swim = Column(Float, default=-0.30)
    mod_beach_tennis = Column(Float, default=-0.20)
    mod_walking = Column(Float, default=-0.10)
    
    # Personal Params
    weight = Column(Float, default=70.0) # kg
    height = Column(Float, default=170.0) # cm
    gender = Column(String, default='Neutral') # Male/Female/Neutral
    
    # Dynamic Modifiers (Emotion)
    mod_stress = Column(Float, default=0.20)
    mod_anxious = Column(Float, default=0.10)
    


class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    glucose = Column(Integer)
    carbs = Column(Integer)
    activity = Column(String)
    emotion = Column(String, default='Calm')

    recommended_dose = Column(Float)
    actual_dose = Column(Float)
    
    # Relationship to feedback
    feedback = relationship("Feedback", uselist=False, back_populates="log")
    # Relationship to adjustments
    adjustments = relationship("Adjustment", back_populates="log", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('logs.id'))
    outcome = Column(String) # "Hypo", "Hyper", "Perfect"
    notes = Column(String)
    
    log = relationship("Log", back_populates="feedback")

class Adjustment(Base):
    __tablename__ = 'adjustments'
    
    id = Column(Integer, primary_key=True)
    ref_log_id = Column(Integer, ForeignKey('logs.id'))
    parameter = Column(String) # e.g. "mod_run"
    old_value = Column(Float)
    new_value = Column(Float)
    rationale = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    
    log = relationship("Log", back_populates="adjustments")

class Food(Base):
    __tablename__ = 'foods'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    measure = Column(String) # e.g. "1 colher de sopa"
    carbs = Column(Float) # g of CHO
    kcal = Column(Integer) # Calories

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True) 
    password_hash = Column(String)
    salt = Column(String)

# Database Setup
DATABASE_URL = "sqlite:///./data/diabetes.db"
os.makedirs("./data", exist_ok=True)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import text
import hashlib
import os

def init_db():
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    # Auto-migration for 'weight' column (Legacy check)
    try:
        session.execute(text("SELECT weight FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding weight column...")
        session.rollback() 
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN weight FLOAT DEFAULT 70.0"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")

    # Auto-migration for 'mod_walking' column
    try:
        session.execute(text("SELECT mod_walking FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding mod_walking column...")
        session.rollback()
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN mod_walking FLOAT DEFAULT -0.10"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")

    # Auto-migration for 'height'
    try:
        session.execute(text("SELECT height FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding height column...")
        session.rollback()
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN height FLOAT DEFAULT 170.0"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")

    # Auto-migration for 'gender'
    try:
        session.execute(text("SELECT gender FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding gender column...")
        session.rollback()
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN gender VARCHAR DEFAULT 'Neutral'"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")

    # Auto-migration for 'mod_stress'
    try:
        session.execute(text("SELECT mod_stress FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding mod_stress column...")
        session.rollback()
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN mod_stress FLOAT DEFAULT 0.20"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")

    # Auto-migration for 'mod_anxious'
    try:
        session.execute(text("SELECT mod_anxious FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding mod_anxious column...")
        session.rollback()
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN mod_anxious FLOAT DEFAULT 0.10"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")

    # Auto-migration for 'emotion' in logs
    try:
        session.execute(text("SELECT emotion FROM logs LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding emotion column to logs...")
        session.rollback()
        try:
            session.execute(text("ALTER TABLE logs ADD COLUMN emotion VARCHAR DEFAULT 'Calm'"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
            
    # Create default settings if not exists
    if session.query(Settings).count() == 0:
        default_settings = Settings()
        session.add(default_settings)
        session.commit()
        
    # Create default admin user if not exists
    if session.query(User).count() == 0:
        print("Creating default admin user...")
        salt = os.urandom(32).hex()
        # Simple sha256 for demo purposes (production should use bcrypt/argon2)
        pwd_hash = hashlib.sha256(("admin" + salt).encode('utf-8')).hexdigest()
        
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=pwd_hash,
            salt=salt
        )
        session.add(admin_user)
        session.commit()
        print("Default user created: admin / admin")
        
    session.close()

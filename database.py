from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

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
    
    # Personal Params
    weight = Column(Float, default=70.0) # kg
    
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
    emotion = Column(String)
    recommended_dose = Column(Float)
    actual_dose = Column(Float)
    
    # Relationship to feedback
    feedback = relationship("Feedback", uselist=False, back_populates="log")
    # Relationship to adjustments
    adjustments = relationship("Adjustment", back_populates="log")

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

# Database Setup
DATABASE_URL = "sqlite:///./diabetes.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import text

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration for 'weight' column
    session = SessionLocal()
    try:
        session.execute(text("SELECT weight FROM settings LIMIT 1"))
    except Exception:
        print("Migrating DB: Adding weight column...")
        session.rollback() # Clear error state
        try:
            session.execute(text("ALTER TABLE settings ADD COLUMN weight FLOAT DEFAULT 70.0"))
            session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
            
    # Create default settings if not exists
    # Now safe to query Settings because schema matches
    if session.query(Settings).count() == 0:
        default_settings = Settings()
        session.add(default_settings)
        session.commit()
    session.close()

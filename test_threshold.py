from database import init_db, SessionLocal, Settings
from calculator import InsulinCalculator

def test_threshold():
    init_db()
    session = SessionLocal()
    settings = session.query(Settings).first()
    
    # Configure test settings
    settings.target_glucose = 90
    settings.isf = 50
    settings.correction_threshold = 120
    session.commit()
    
    calc = InsulinCalculator(settings)
    
    print("--- Threshold Logic Test ---")
    
    # Case 1: Glucose 110 (Above target 90, but below threshold 120) -> Should be 0 correction
    res1 = calc.calculate_dose(110, 0, "None", "Calm", [])
    print(f"Test 1 (110 mg/dL): Correction Expected 0.0. Got: {res1['correction_dose']}")
    
    # Case 2: Glucose 130 (Above threshold 120) -> Should correct to target 90
    # Correction = (130 - 90) / 50 = 40 / 50 = 0.8
    res2 = calc.calculate_dose(130, 0, "None", "Calm", [])
    print(f"Test 2 (130 mg/dL): Correction Expected 0.8. Got: {res2['correction_dose']}")

    session.close()

if __name__ == "__main__":
    test_threshold()

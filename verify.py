from database import init_db, SessionLocal, Settings, Log
from calculator import InsulinCalculator
from datetime import datetime

def test_calculator():
    # Setup DB
    init_db()
    session = SessionLocal()
    
    # Ensure settings exist (init_db creates default)
    settings = session.query(Settings).first()
    
    # Create a mock calculator
    # Mock time? For now we assume verify run in "Day" time or just handle defaults.
    # But get_icr checks datetime.now(). The default ICRs are different. 
    # Let's force a specific ICR by mocking settings or just accepting whatever time it is.
    # To be deterministic, let's update settings to be uniform for the test?
    # Or just print what ICR was used.
    
    # Set uniform ICR for testing simplicity
    settings.icr_breakfast = 10.0
    settings.icr_lunch = 10.0
    settings.icr_dinner = 10.0
    settings.icr_snack = 10.0
    session.commit()
    
    calc = InsulinCalculator(settings)
    
    print(f"--- Telemetry for Verify ---")
    
    # Test 1: Basic
    # Glucose 200, Target 100, ISF 50 -> Correction = (200-100)/50 = 2.0
    # Carbs 50, ICR 10 -> Carb = 5.0
    # Gross = 7.0
    res = calc.calculate_dose(200, 50, "None", "Calm", [])
    print(f"Test 1 (Basic 200mg/dL, 50g): Gross Expected 7.0. Got Gross: {res['gross_dose']}")
    print(f"Recommended: {res['recommended_dose']}")
    
    # Test 2: Priority Rule
    # "Running" (-30%) AND "Stress" (+20%)
    # Logic: Ignore Stress (20%). Use Running (-30%). 
    # Net modifier: -0.30
    # Expected Adjusted Dose: 7.0 * (1 - 0.30) = 4.9
    # Recommended (Rounded): 5.0 (nearest 0.5)
    
    res2 = calc.calculate_dose(200, 50, "Running", "Stress", [])
    print(f"Test 2 (Running + Stress): Modifier Expected -0.30. Got: {res2['final_modifier_used']}")
    print(f"Final Dose Raw: {res2['final_dose_raw']}")
    
    if abs(res2['final_modifier_used'] - (-0.30)) < 0.001:
        print("PASS: Priority Rule Correct")
    else:
        print(f"FAIL: Priority Rule Incorrect (Got {res2['final_modifier_used']})")

    session.close()

if __name__ == "__main__":
    test_calculator()

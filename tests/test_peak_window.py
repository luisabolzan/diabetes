from src.calculator import InsulinCalculator
from src.database import Settings, Log
from datetime import datetime, timedelta

def test_peak_window():
    print("Testing Peak Window Logic (60-120 min)...")
    
    settings = Settings(
        icr_breakfast=10.0, icr_lunch=10.0, icr_dinner=10.0, icr_snack=10.0,
        isf=50.0, target_glucose=100, correction_threshold=120,
        mod_run=-0.30, mod_stress=0.0, mod_anxious=0.0, mod_gym=0.0, mod_swim=0.0, mod_beach_tennis=-0.20
    )
    
    calc = InsulinCalculator(settings)
    
    now = datetime.now()
    
    # CASE 1: IN WINDOW (90 mins ago) + ACTIVE
    print("\n--- CASE 1: 90 mins ago (PEAK) + Running ---")
    log_peak = Log(
        timestamp=now - timedelta(minutes=90),
        actual_dose=5.0, glucose=150, carbs=50, activity="None"
    )
    res_peak = calc.calculate_dose(150, 50, "Running", "Calm", [log_peak])
    print(f"Risk State: {res_peak.get('risk_state')}")
    print(f"Modifier Used: {res_peak['final_modifier_used']:.2f}")
    
    if res_peak.get('risk_state') == "HIGH" and res_peak['final_modifier_used'] == -0.50:
        print("✅ PASS: High Risk detected, -50% applied.")
    else:
        print("❌ FAIL: Window logic incorrect.")

    # CASE 2: OUT OF WINDOW (150 mins ago) + ACTIVE
    print("\n--- CASE 2: 150 mins ago (TAIL) + Running ---")
    log_tail = Log(
        timestamp=now - timedelta(minutes=150),
        actual_dose=5.0, glucose=150, carbs=50, activity="None"
    )
    res_tail = calc.calculate_dose(150, 50, "Running", "Calm", [log_tail])
    print(f"Risk State: {res_tail.get('risk_state')}")
    print(f"Modifier Used: {res_tail['final_modifier_used']:.2f}")
    
    # Standard Running mod is -0.30
    if res_tail.get('risk_state') == "LOW" and abs(res_tail['final_modifier_used'] - (-0.30)) < 0.01:
        print("✅ PASS: Safe Tail detected, standard modifier applied.")
    else:
        print(f"❌ FAIL: Tail logic incorrect (Mod: {res_tail['final_modifier_used']}).")

if __name__ == "__main__":
    test_peak_window()

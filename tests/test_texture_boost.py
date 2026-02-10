import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.predict import apply_smart_calibration

def test_tiered_logic():
    print("--- Testing Texture Logic Tiers ---")
    
    # Case 1: "Carreteiro" (High Density, Trigger Boost)
    # Raw=9.0 (Low), Texture=40.0% (High Density)
    # Expect: (9 * 2.5) + 30 = 22.5 + 30 = 52.5g
    raw_1 = 9.0
    tex_1 = 40.0
    res_1, msg_1 = apply_smart_calibration(raw_1, tex_1)
    print(f"Case 1 (Carreteiro): Raw={raw_1}, Texture={tex_1}%")
    print(f"  -> Result: {res_1:.2f}g (Expected ~52.5g)")
    print(f"  -> Message: {msg_1}")
    if "HIGH DENSITY BOOST" in (msg_1 or ""):
        print("  [SUCCESS] High Density Boost triggered.")
    else:
        print("  [FAILURE] Wrong logic applied.")
        
    print("-" * 30)

    # Case 2: "White Rice" (Medium Density, Standard Override)
    # Raw=6.0 (Very Low), Texture=20.0% (Medium)
    # Expect: (6 * 2.3) + 18 = 13.8 + 18 = 31.8g
    raw_2 = 6.0
    tex_2 = 20.0
    res_2, msg_2 = apply_smart_calibration(raw_2, tex_2)
    print(f"Case 2 (White Rice): Raw={raw_2}, Texture={tex_2}%")
    print(f"  -> Result: {res_2:.2f}g (Expected ~31.8g)")
    print(f"  -> Message: {msg_2}")
    if "TEXTURE OVERRIDE" in (msg_2 or ""):
        print("  [SUCCESS] Standard Override triggered.")
    else:
        print("  [FAILURE] Wrong logic applied.")

    print("-" * 30)

    # Case 3: "Empty/Plain Plate" (Low Texture, Default Curve)
    # Raw=6.0 (Very Low), Texture=5.0% (Low)
    # Expect: Standard curve (6 * 2.3) + 18 = 31.8g
    # But MSG should be None or Default
    raw_3 = 6.0
    tex_3 = 5.0
    res_3, msg_3 = apply_smart_calibration(raw_3, tex_3)
    print(f"Case 3 (Plain Plate): Raw={raw_3}, Texture={tex_3}%")
    print(f"  -> Result: {res_3:.2f}g")
    print(f"  -> Message: {msg_3}")
    if msg_3 is None:
        print("  [SUCCESS] No override triggered (Default Curve).")
    else:
        print(f"  [FAILURE] Unexpected override: {msg_3}")

if __name__ == "__main__":
    test_tiered_logic()

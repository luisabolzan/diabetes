import cv2
import numpy as np
import io
from PIL import Image
from src.predict import calculate_texture_area, apply_smart_calibration

def create_local_dummy_image(texture_type="flat"):
    # Create 640x480 image
    img = np.full((480, 640, 3), 128, dtype=np.uint8) # Gray background to see noise
    
    if texture_type == "noise":
        # Add random noise to simulate rice
        noise = np.random.normal(0, 35, img.shape).astype(np.int16) # Use int16 to allow +/-
        img = img.astype(np.int16) + noise
        img = np.clip(img, 0, 255).astype(np.uint8)

    
    # Encode to bytes
    is_success, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()

def test_texture_analysis():
    print("--- Testing Texture Analysis ---")
    
    # 1. Test Flat White Image (Plate)
    flat_bytes = create_local_dummy_image("flat")
    flat_pct = calculate_texture_area(flat_bytes)
    print(f"Flat Image Texture: {flat_pct:.2f}% (Expected ~0%)")
    
    # 2. Test Textured Image (Rice)
    noise_bytes = create_local_dummy_image("noise")
    noise_pct = calculate_texture_area(noise_bytes)
    print(f"Noisy Image Texture: {noise_pct:.2f}% (Expected > 0%)")
    
    if flat_pct < 5.0 and noise_pct > 20.0:
        print("SUCCESS: Texture detection works as expected.")
    else:
        print("FAILURE: Texture detection logic needs tuning.")
        
    print("\n--- Testing Logic Override ---")
    # Case A: Low Prediction, Low Texture (Empty Plate?)
    # Raw=5.0, Texture=2.0 -> Should use formula? 
    # Current logic: always uses formula, but flag is False.
    res_a, flag_a = apply_smart_calibration(5.0, 2.0)
    print(f"Case A (Low Raw, Low Texture): {res_a:.2f}g, Override={flag_a} (Expected False)")
    
    # Case B: Low Prediction, High Texture (Hidden Rice)
    # Raw=5.0, Texture=60.0 -> Should use formula, flag True.
    res_b, flag_b = apply_smart_calibration(5.0, 60.0)
    print(f"Case B (Low Raw, High Texture): {res_b:.2f}g, Override={flag_b} (Expected True)")

if __name__ == "__main__":
    test_texture_analysis()

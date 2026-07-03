import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import get_all_food_options
from src.database import SessionLocal, Food

def test_meal_builder():
    print("=== Testing Meal Builder Database Queries ===")
    
    # 1. Fetch all food options
    options = get_all_food_options()
    print(f"Total food options returned: {len(options)}")
    
    if len(options) == 0:
        print("FAIL: No food options returned from database!")
        sys.exit(1)
        
    # 2. Check for sample items in options
    samples = ["Abacaxi", "Arroz branco cozido", "Bolo de cenoura"]
    found_samples = 0
    for key, value in options.items():
        for sample in samples:
            if sample in value:
                print(f"SUCCESS: Found sample '{sample}' with ID {key}: {value}")
                found_samples += 1
                break
                
    if found_samples == 0:
        print("FAIL: None of the sample foods were found in options!")
        sys.exit(1)
        
    # 3. Simulate Plate logic
    print("\n=== Simulating Plate Logic ===")
    plate_items = []
    session = SessionLocal()
    
    # Let's take the first 3 foods from the database
    foods = session.query(Food).limit(3).all()
    for food in foods:
        print(f"Adding to plate: {food.name} ({food.measure}) - {food.carbs}g CHO")
        plate_items.append(food)
        
    total_carbs = sum(f.carbs for f in plate_items)
    total_kcal = sum(f.kcal for f in plate_items)
    
    print(f"Simulated Plate - Total Carbs: {total_carbs}g | Total Kcal: {total_kcal}")
    
    assert total_carbs > 0, "Total carbs should be greater than 0"
    print("SUCCESS: Plate simulation completed successfully!")
    
    session.close()

if __name__ == "__main__":
    test_meal_builder()

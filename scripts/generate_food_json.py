import json
import re
import os

def parse_food_table(md_path, json_path):
    foods = []
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        # Regex to match table row: | Name | Measure | Carbs | Kcal |
        # Example: | Bolo simples | fatia média | 33.0 | 263.0 |
        match = re.search(r'\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*([\d\.,]+)\s*\|\s*([\d\.,]+)\s*\|', line)
        if match:
            try:
                name = match.group(1).strip()
                measure = match.group(2).strip()
                carbs = float(match.group(3).replace(',', '.'))
                kcal = float(match.group(4).replace(',', '.'))
                
                # Filter out headers or bad data
                if name.lower() == "nome do alimento" or carbs == 0.0 and kcal == 0.0 and name == "": 
                    continue

                foods.append({
                    "name": name,
                    "measure": measure,
                    "carbs": carbs,
                    "kcal": int(kcal),
                    "id": len(foods) + 1
                })
            except ValueError:
                continue
                
    print(f"Parsed {len(foods)} food items.")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(foods, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to {json_path}")

if __name__ == "__main__":
    MD_FILE = "data/food_table.md"
    JSON_FILE = "mobile-ios-pwa/src/data/foods.json"
    parse_food_table(MD_FILE, JSON_FILE)

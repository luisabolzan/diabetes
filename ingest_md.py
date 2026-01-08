from database import init_db, SessionLocal, Food
import re

def ingest():
    init_db()
    session = SessionLocal()
    
    # Check if we already have data and clear it
    session.query(Food).delete()
    session.commit()
    print("Cleared existing food data.")

    filename = "food_table.md"
    count = 0
    
    print(f"Reading {filename}...")
    
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Regex to capture the table row content
    # Format: | Name | Measure | CHO |
    # We need to be careful with formatting inside the cells if any
    
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
            
        # Remove leading/trailing pipes
        content = line.strip("|")
        parts = content.split("|")
        
        if len(parts) < 3:
            continue
            
        # Basic cleanup of parts
        raw_name = parts[0].strip()
        raw_measure = parts[1].strip()
        raw_cho = parts[2].strip()
        
        # Skip header lines
        if "Nome do Alimento" in raw_name or "---" in raw_name or "Edição n" in raw_name:
            continue
            
        try:
            # Parse CHO
            # Sometimes it might fail if emptiness or weird chars
            if not raw_cho:
                continue
            
            # Remove any trailing invalid chars if needed, though float() handles some
            cho = float(raw_cho)
            
            # Name and Measure
            name = raw_name
            measure = raw_measure
            
            # Create object
            f = Food(name=name, measure=measure, carbs=cho)
            session.add(f)
            count += 1
            
        except ValueError:
            # print(f"Skipping line: {line}")
            continue
            
    session.commit()
    session.close()
    print(f"Successfully ingested {count} food items from markdown.")

if __name__ == "__main__":
    ingest()

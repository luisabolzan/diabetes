from src.database import SessionLocal, Food

def verify():
    session = SessionLocal()
    count = session.query(Food).count()
    print(f"Total Food Items: {count}")
    
    # Check specific items
    samples = ["Abacaxi", "Bolo de cenoura", "Arroz branco cozido"]
    for s in samples:
        item = session.query(Food).filter(Food.name.like(f"%{s}%")).first()
        if item:
            print(f"Found '{s}': {item.name} | {item.measure} | {item.carbs}g")
        else:
            print(f"WARNING: Could not find '{s}'")
    
    session.close()

if __name__ == "__main__":
    verify()

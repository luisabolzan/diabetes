from database import SessionLocal, Food

def verify():
    session = SessionLocal()
    count = session.query(Food).count()
    print(f"Total items: {count}")
    
    foods = session.query(Food).limit(10).all()
    for f in foods:
        try:
            print(f"Name: {f.name} | Measure: {f.measure} | Carbs: {f.carbs}")
        except UnicodeEncodeError:
            print(f"Name: {f.name.encode('ascii', 'replace').decode()} | Measure: {f.measure.encode('ascii', 'replace').decode()} | Carbs: {f.carbs}")
    session.close()

if __name__ == "__main__":
    verify()

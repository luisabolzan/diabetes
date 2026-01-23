from pypdf import PdfReader
from src.database import init_db, SessionLocal, Food
import re

def ingest():
    init_db()
    session = SessionLocal()
    
    # Check if we already have data
    # Clear existing data to allow re-ingestion with better logic
    session.query(Food).delete()
    session.commit()
    print("Cleared existing food data.")

    reader = PdfReader("data/manual-carboidratos.pdf")
    count = 0
    
    print(f"Processing {len(reader.pages)} pages...")
    
    # Heuristic parsing logic
    # The PDF likely has lines like "Rice, white ... 1 cup ... 45"
    # We will try to extract lines that end with a number (CHO)
    
    for page in reader.pages:
        text = page.extract_text()
        lines = text.split('\n')
        
        for line in lines:
            # Clean common headers/footers if needed
            if "Medida usual" in line or "g de CHO" in line:
                continue
            
            # Skip Table of Contents (many dots)
            if "..." in line or ".." in line:
                continue
                
            # Skip likely chapter headers (start with number dot)
            if re.match(r'^\d+\.', line.strip()):
                continue
                
            # Regex to find structure: Name ... Measure ... Cho
            # This is tricky without seeing the PDF. Let's assume a generic strategy:
            # Look for lines ending in a number (int or float)
            # Example: "Arroz branco cozido 1 colher de sopa cheia 5"
            
            # Strategy: The columns are likely: Name | Measure | Weight(g) | CHO(g) | Kcal
            # We want CHO, which is likely the 2nd to last number if Kcal is present.
            
            parts = line.strip().split()
            if not parts:
                continue
                
            try:
                # Helper to check if a string is a valid number (handling comma)
                def is_num(s):
                    return s.replace(',', '.', 1).replace('.', '', 1).isdigit()
                
                # Check last 3 parts
                p_last = parts[-1].replace(',', '.')
                p_2nd = parts[-2].replace(',', '.') if len(parts) > 1 else "x"
                p_3rd = parts[-3].replace(',', '.') if len(parts) > 2 else "x"
                
                kcal = 0
                cho = 0.0
                
                # Context: Weight | CHO | Kcal (3 numbers at end)
                if len(parts) >= 3 and is_num(parts[-1]) and is_num(parts[-2]) and is_num(parts[-3]):
                    kcal = int(float(p_last))
                    cho = float(p_2nd)
                    name_end = -3
                # Context: CHO | Kcal (2 numbers at end)
                # Assuming the format is consistently CHO then Kcal if 2 numbers exist
                elif len(parts) >= 2 and is_num(parts[-1]) and is_num(parts[-2]):
                     kcal = int(float(p_last))
                     cho = float(p_2nd)
                     name_end = -2
                # Context: Just CHO (1 number)
                elif len(parts) >= 1 and is_num(parts[-1]):
                    cho = float(p_last)
                    kcal = 0 # No kcal data
                    name_end = -1
                else:
                    continue
                
                # Check if reasonable carb count (0 to 200)
                if cho < 0 or cho > 200:
                    continue
                    
                # Everything else is the name/measure
                description = " ".join(parts[:name_end])
                
                # Basic cleaning
                if len(description) < 3: 
                    continue
                    
                # Attempt to split measure if possible, otherwise put all in Name
                # Common measures: "colher", "fatia", "unidade", "xícara", "copo"
                # This is "best effort"
                
                measure = "Porção"
                name = description
                
                # Try to find where measure starts
                # Keywords for measures in pt-BR
                measure_keywords = ["colher", "fatia", "unidade", "xícara", "copo", "pedaço", "concha", "escumadeira"]
                
                split_idx = -1
                for key in measure_keywords:
                    if key in description.lower():
                        # Find the index of this keyword
                        try:
                            # We want the word index in 'parts' list actually
                            # Re-scanning parts
                            for i, p in enumerate(parts[:-1]):
                                if key in p.lower():
                                    split_idx = i
                                    # Check if there is a number before it (e.g., "1 colher")
                                    if i > 0 and parts[i-1].replace('.', '', 1).isdigit():
                                        split_idx = i - 1
                                    break
                        except:
                            pass
                    if split_idx != -1:
                        break
                
                if split_idx != -1:
                    name = " ".join(parts[:split_idx])
                    measure = " ".join(parts[split_idx:-1])
                
                f = Food(name=name, measure=measure, carbs=cho, kcal=kcal)
                session.add(f)
                count += 1
                
            except ValueError:
                # Not a carb line
                continue
    
    session.commit()
    session.close()
    print(f"Successfully ingested {count} food items.")

if __name__ == "__main__":
    ingest()

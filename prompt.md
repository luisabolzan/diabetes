**Role:** Act as a Senior Full-Stack Developer and Data Scientist.

**Goal:** Create a comprehensive technical specification and core code structure for a **Diabetes Management & Insulin Calculator Application**. The application should function as a responsive Website, but be packaging-ready for a PC Desktop app (using Electron or similar).

**Core Logic:**
The app acts as a "Smart Bolus Calculator." It calculates insulin dosage based on a base Insulin-to-Carb Ratio (ICR) and Correction Factor (ISF), but adjusts dynamically based on contextual variables (Activity & Emotion).

**Key Features & Requirements:**

**0. Download any necessary libraries.**

**1. User Configuration (Settings):**

* **Time-Based ICR:** Allow the user to set distinct Insulin-to-Carb Ratios for different times of day (e.g., Breakfast 1:10, Lunch 1:15, Dinner 1:20).
* **Sensitivity Factor (ISF):** Allow the user to set their Correction Factor (e.g., 1 unit drops glucose by 50 mg/dL).
* **Duration of Insulin Action:** A setting to define how long insulin lasts in the user's body (usually 3-5 hours) for IOB calculations.

**2. The Calculator Interface (Main Dashboard):**

* **Inputs:**
* Current Blood Glucose (mg/dL).
* Carbs to be eaten (g) — *Bonus: Integrate a food API (like Nutritionix) to auto-fill carbs based on food name.*
* Physical Activity (Selectable list: Gym/Weights, Running, Swimming, Yoga, None).
* Emotional State (Selectable list: Stress, Calm, Anxious).


* **The "Smart" Algorithm:**
* **Base Calculation:** `(Carbs / ICR) + ((Current Glucose - Target Glucose) / ISF)`.
* **Active Insulin (IOB):** Calculate "Insulin on Board" from previous doses and subtract it from the total to prevent stacking (hypoglycemia).
* **Contextual Modifiers:** Apply a percentage modifier to the dose based on tags.
* **Research Requirement:** You must define default behaviors for the exercise types based on medical data (e.g., Aerobic usually lowers glucose, intense Anaerobic might spike it).
* **Priority Rule:** If both Stress (usually raises glucose) and Exercise (usually lowers glucose) are present, the **Exercise factor must take priority** to prevent dangerous lows.



**3. Decision Support:**

* If the calculation results in a decimal (e.g., 1.6 units), advise on rounding logic based on the user's historical sensitivity.

**4. Feedback Loop (Machine Learning/Heuristics):**

* After the meal (e.g., 2 hours later), the user must be able to log the result (e.g., "Went Hypo," "Perfect," "Went Hyper").
* The system should store this data to adjust future recommendations (e.g., "Last time you ate 22g carbs with 'Running', 2 units caused hypoglycemia. Suggesting 1 unit today").

**5. History & Analytics:**

* A log view showing past entries, doses, and outcomes.
* **Export:** A feature to export data to CSV/PDF for sharing with doctors.

**Deliverables:**

**1. Tech Stack Selection:**
* FastAPI/Flask + Streamlit/NiceGUI + Pandas/NumPy + SQLite + PyWebView.

**2. Algorithm Design:**
Write the pseudo-code or Python logic for the "Smart Calculation Algorithm," specifically focusing on the **Priority Rule** (Exercise > Stress) and the **IOB subtraction**.

**3. Database Schema:**
Design the SQL schema to store User Settings, Logs, and the Feedback loop data.
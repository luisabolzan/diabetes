
# ANTIGRAVITY
### Type 1 Diabetes Management & Adaptive Bolus Calculator

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python) ![NiceGUI](https://img.shields.io/badge/UI-NiceGUI-orange?style=for-the-badge) ![Status](https://img.shields.io/badge/Status-Experimental-red?style=for-the-badge)

## About
**Antigravity** is a next-generation bolus calculator designed for Type 1 Diabetics seeking precision control. Unlike standard calculators that rely on static ratios, Antigravity uses a **context-aware engine** that adapts to your biology in real-time. By integrating physical activity, emotional state, and dynamic feedback loops, it attempts to "defy" the unpredictability of blood glucose.

---

## 🚀 Key Features

### 1. Adaptive & Context-Aware Logic
The calculator moves beyond simple I:C ratios. It applies sophisticated dynamic modifiers based on your current state:
*   **Activity Modifiers**: Automatically adjusts for aerobic vs anaerobic impact.
    *   *Running/Swimming*: **-30%** (Aerobic reduction)
    *   *Beach Tennis*: **-20%** (Moderate aerobic)
    *   *Gym/Weights*: **+10%** (Anaerobic rise)
*   **Emotional Context**: Accounts for cortisol-induced spikes.
    *   *Stress*: **+20%**
*   **Feedback Loop**: The "Algorithm Within" learns from your logs. If you report a "Hypo" or "Hyper" event, the system auto-tunes your personal modifiers for future accuracy.

### 2. Safety-First: The "Peak Window"
We abandoned the traditional linear "Duration of Action" curve in favor of a stricter safety protocol.
*   **Critical Danger Zone**: The system creates a hard lock on the **60-120 minute** window post-bolus.
*   **Logic**: If exercise is detected within this peak insulin action window, the calculator triggers a **Maximum Safety Protocol**, applying a hard **-50% reduction** to prevent dangerous hypoglycemia.
*   **Visual Status**: A live dashboard monitors this window, displaying **⚠️ PEAK ACTION** (High Risk) vs **✅ SAFE TAIL** (Low Risk).

### 3. Data-Driven Meal Builder
Integrated with the comprehensive `manual-carboidratos.pdf` database (SBD/UFRGS), the app puts **1,200+ localized food items** at your fingertips.
*   **Virtual Plate**: Search and combine multiple items (e.g., "Arroz Branco" + "Feijão").
*   **Auto-Sum**: Automatically calculates total carbohydrates for precise dosing.

---

## 🛠️ Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/luisabolzan/diabetes.git
    cd diabetes
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database**
    On first run, the system will automatically generate `diabetes.db` and ingest the food table.
    *(Note: Maintain `food_table.md` in the root directory for data ingestion)*.

---

## 💻 Usage

1.  **Run the Application**
    ```bash
    python main.py
    ```
    The interface will launch in your default web browser (Port 8081).

2.  **Check Status**: Glance at the top dashboard to see your current Risk State (Peak vs Safe).
3.  **Build a Meal**: Click "Open Meal Builder" to search for foods and fill your carb count.
4.  **Calculate**: Select your Activity and Emotion, then click Calculate. The app will provide a recommended dose with detailed logic explanations.
5.  **Log & Learn**: Save the log. Later, use the **History Tab** to provide feedback ("Perfect", "Hypo", "Hyper") and watch the algorithm adapt your settings.

---

## ⚠️ Medical Disclaimer
**THIS SOFTWARE IS FOR EXPERIMENTAL AND EDUCATIONAL PURPOSES ONLY.**

It is **NOT** a certified medical device. The specific algorithms (Peak Window, Adaptive Modifiers) are experimental implementations. **Always** follow the advice of your endocrinologist and use your standard glucose meter/CGM for treatment decisions. The developer assumes no liability for health outcomes.

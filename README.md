# ANTIGRAVITY: Hybrid Vision Bolus Calculator

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python) ![NiceGUI](https://img.shields.io/badge/UI-NiceGUI-orange?style=for-the-badge) ![Database](https://img.shields.io/badge/Database-SQLite-lightgrey?style=for-the-badge) ![Status](https://img.shields.io/badge/Status-Experimental-red?style=for-the-badge)

## About
**Diabetes Manager** is an advanced, context-aware insulin calculator for Type 1 Diabetics, specifically engineered to solve the "invisible food" problem in computer vision. It combines a **Deep Learning semantic layer** (ResNet18) with a **Classic CV texture layer** to estimate carbohydrate content in low-contrast meals (e.g., white rice on white plates) that standard AI models often miss.

Beyond vision, it features a safety-first **"Peak Window" logic** that prevents dangerous insulin stacking during exercise and adapts dynamically to both physical activities and emotional states.

---

## 🚀 Key Features

### 1. Hybrid Computer Vision (RGB + Texture)
Combines two layers of analysis to ensure no carb is left uncounted:
*   **Semantic Layer (ResNet18)**: Identifies food types and estimates standard portions.
*   **Texture Layer (Laplacian Variance)**: Detects surface roughness to "see" volume in monochromatic dishes.
    *   *Safety Floor*: If the AI sees < 10g but texture is high, the system enforces a minimum safety count (defaulting to ~30g).
    *   *Density Boost*: For complex mixed dishes (like "Carreteiro"), high texture density triggers a boost multiplier.

### 2. SQLite-Backed Local Authentication
Fully self-contained user registry and authentication system:
*   No external APIs or cloud services (like Supabase) are required.
*   Secure local password hashing using `SHA256` and random cryptographic `salt`.
*   Auto-migration schema: The database automatically initializes and updates its columns (e.g., adding sports, personal parameters, and custom values) on startup.
*   **Default Admin Account**:
    *   **Email:** `admin@example.com`
    *   **Password:** `admin`

### 3. Context-Aware Modifiers (Activity & Emotion)
Instead of static ratios, Antigravity adjusts dynamically for:
*   **Physical Activities**:
    *   *Aerobic (Walking, Running, Swimming, Beach Tennis)*: Reduces bolus dynamically (up to ~30%) to prevent hypoglycemia.
    *   *Anaerobic (Gym/Weights)*: Increases bolus (~10%) to counteract stress-induced spikes.
*   **Emotional States**:
    *   *Stress / Anxiety*: Adjusts insulin sensitivity parameters (+20% for stress, +10% for anxiety) to manage hormone-induced hyperglycemia.
    *   *Priority Rule*: If physical activity reduces the dose and emotional factors increase it, the safety protocol prioritizes the activity modifier to prevent drops.

### 4. Safety-First "Peak Window" Logic
Prevents hypoglycemia during physical activity:
*   **The Problem**: Exercise increases insulin sensitivity. Correcting a high blood sugar *during* the peak action of a previous dose can lead to a crash.
*   **The Solution**: The system monitors the **60-120 minute window** post-bolus.
    *   If exercise is detected within this window, a **hard safety lock reduces the dose by 50%**, warning the user with a **⚠️ PEAK ACTION** notification.
    *   Outside this window, it switches to **✅ SAFE TAIL**, allowing standard corrections.

---

## 🛠️ Installation & Run

### Prerequisites
*   Python 3.10+
*   (Optional) CUDA-capable GPU for faster PyTorch vision calculations

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/luisabolzan/diabetes.git
    cd diabetes
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If deploying to a restricted environment, remove `torch` and `torchvision` from requirements. The app will auto-switch to Lite Mode.*

3.  **Run the Application**
    ```bash
    python main.py
    ```
    The interface will launch in your default web browser at `http://localhost:8080`.

---

## 💻 Usage Flow

1.  **Check Status**: Top dashboard shows your current IOB (Insulin on Board) safety risk state based on the time since your last dose.
2.  **Build Meal**:
    *   **Vision**: Upload a photo. The Hybrid Engine estimates carbs.
    *   **Manual**: Search the integrated localized food database.
3.  **Set Context**: Select your physical activity, duration, intensity, and current emotional state (Calm, Stress, Anxious).
4.  **Calculate**: The system processes glucose levels, carbs, activity, emotion, and active history.
    *   *Result*: A specific dose recommendation with detailed calculation breakdown.
5.  **Log & Learn**: Save the log. Use the History tab later to review logs, save feedback, or delete entries.

---

## ⚠️ Medical Disclaimer
**THIS SOFTWARE IS FOR EXPERIMENTAL AND EDUCATIONAL PURPOSES ONLY.**

It is **NOT** a certified medical device. The specific algorithms (Peak Window, Adaptive Modifiers, Hybrid Vision) are experimental implementations. **Always** follow the advice of your endocrinologist and use your standard glucose meter/CGM for treatment decisions. The developer assumes no liability for health outcomes.

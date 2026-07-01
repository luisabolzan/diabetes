# ANTIGRAVITY: Hybrid Vision Bolus Calculator

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python) ![NiceGUI](https://img.shields.io/badge/UI-NiceGUI-orange?style=for-the-badge) ![Status](https://img.shields.io/badge/Status-Experimental-red?style=for-the-badge)

## About
**Antigravity** is an advanced, context-aware insulin calculator for Type 1 Diabetics, specifically engineered to solve the "invisible food" problem in computer vision. It combines a **Deep Learning semantic layer** (ResNet18) with a **Classic CV texture layer** to accurately estimate carbohydrate content in low-contrast meals (e.g., white rice on white plates) that standard AI models often miss.

Beyond vision, it features a safety-first "Peak Window" logic that prevents dangerous insulin stacking during exercise, adapting dynamically to your physical activity.

---

## 🚀 Key Features

### 1. Hybrid Computer Vision (RGB + Texture)
Combines two layers of analysis to ensure no carb is left uncounted:
*   **Semantic Layer (ResNet18)**: Identifies food types and estimates standard portions.
*   **Texture Layer (Laplacian Variance)**: Detects surface roughness to "see" volume in monochromatic dishes (e.g., Rice, Mashed Potatoes).
    *   *Safety Floor*: If the AI sees <10g but texture is high, the system enforces a minimum safety count (defaulting to ~30g).
    *   *Density Boost*: For complex mixed dishes (like "Carreteiro"), high texture density triggers a boost multiplier to match real-world caloric density.

### 2. Safety-First "Peak Window" Logic
Prevents hypoglycemia during physical activity:
*   **The Problem**: Exercise increases insulin sensitivity. Correcting a high blood sugar *during* the peak action of a previous dose can lead to a crash.
*   **The Solution**: The system monitors the **60-120 minute window** post-bolus.
    *   If exercise is detected within this window, a **hard lock reduces the dose** or warns the user, visualizing the risk as **⚠️ PEAK ACTION**.
    *   Outside this window, it switches to **✅ SAFE TAIL**, allowing standard corrections.

### 3. Context-Aware Modifiers
Instead of static ratios, Antigravity adjusts for activity types:
*   **Aerobic (Run/Swim)**: Reduces bolus by ~30% to prevent drops.
*   **Anaerobic (Gym/Weights)**: Increases bolus by ~10% to counteract stress-induced spikes.
*   **Heuristic Learning**: The "Algorithm Within" learns from your logs. Reported a "Hypo"? It auto-tunes your modifiers for next time.

### 4. Deploy Anywhere (Lite Mode)
Built for flexibility:
*   **Full Mode (Local)**: Uses PyTorch for full AI vision capabilities.
*   **Lite Mode (Cloud/Vercel)**: Automatically detects if PyTorch is missing (due to slug size limits) and degrades gracefully to a manual-entry calculator with all the safety logic intact.

---

## 🛠️ Installation

### Prerequisites
*   Python 3.10+
*   (Optional) CUDA-capable GPU for faster inference

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/luisabolzan/diabetes.git
    cd diabetes
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If deploying to a restricted environment (like Vercel free tier), remove `torch` and `torchvision` from requirements. The app will auto-switch to Lite Mode.*

3.  **Run the Application**
    ```bash
    python main.py
    ```
    The interface will launch in your default web browser at `http://localhost:8080`.

---

## 💻 Usage Flow

1.  **Check Status**: Top dashboard shows your current IOB (Insulin on Board) risk state.
2.  **Build Meal**:
    *   **Vision**: Upload a photo. The Hybrid Engine will estimate carbs.
    *   **Manual**: Search the integrated localized food database (1200+ items).
3.  **Set Context**: Select your activity (e.g., "Going for a Run").
4.  **Calculate**: The system processes Glucose + Carbs + Activity + history.
    *   *Result*: A specific dose recommendation with a breakdown of "Why?" (e.g., "-30% due to Running").
5.  **Log & Learn**: Save the log. Use the History tab later to report "Hypo" or "Perfect" to train your personal algorithm.

---

## ⚠️ Medical Disclaimer
**THIS SOFTWARE IS FOR EXPERIMENTAL AND EDUCATIONAL PURPOSES ONLY.**

It is **NOT** a certified medical device. The specific algorithms (Peak Window, Adaptive Modifiers, Hybrid Vision) are experimental implementations. **Always** follow the advice of your endocrinologist and use your standard glucose meter/CGM for treatment decisions. The developer assumes no liability for health outcomes.

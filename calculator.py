from datetime import datetime, timedelta
from database import Settings, Log
from typing import List, Optional

class InsulinCalculator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_icr(self, current_time: datetime) -> float:
        hour = current_time.hour
        # Simple time-based logic (configurable ranges could be added later)
        # 06:00 - 10:59 -> Breakfast
        # 11:00 - 16:59 -> Lunch
        # 17:00 - 23:59 -> Dinner
        # 00:00 - 05:59 -> Snack/Night uses Dinner or Snack ratio? Let's use Snack as default fallback or specific logic.
        
        if 6 <= hour < 11:
            return self.settings.icr_breakfast
        elif 11 <= hour < 17:
            return self.settings.icr_lunch
        elif 17 <= hour <= 23:
            return self.settings.icr_dinner
        else:
            return self.settings.icr_snack # Night/Late snack

    # calculate_iob removed as requested


    def calculate_dose(self, 
                       current_glucose: int, 
                       carbs: int, 
                       activity: str, 
                       emotion: str, 
                       history: List[Log],
                       manual_last_bolus_min: Optional[int] = None) -> dict:
        
        current_time = datetime.now()
        
        # 1. Base Components
        icr = self.get_icr(current_time)
        carb_insulin = carbs / icr
        
        target = self.settings.target_glucose
        threshold = self.settings.correction_threshold
        
        if current_glucose >= threshold:
            correction_insulin = (current_glucose - target) / self.settings.isf
        else:
            correction_insulin = 0.0
        
        gross_insulin = carb_insulin + correction_insulin
        
        # 2. Contextual Modifiers
        modifier_percent = 0.0
        
        # Activity Factors (Dynamic)
        activity_factors = {
            "Gym/Weights": self.settings.mod_gym,
            "Running": self.settings.mod_run,
            "Swimming": self.settings.mod_swim,
            "Beach Tennis": self.settings.mod_beach_tennis,
            "None": 0.0
        }
        
        # Emotion Factors (Dynamic)
        emotion_factors = {
            "Stress": self.settings.mod_stress,
            "Anxious": self.settings.mod_anxious,
            "Calm": 0.0
        }
        
        act_mod = activity_factors.get(activity, 0.0)
        emo_mod = emotion_factors.get(emotion, 0.0)
        
        # Priority Rule: If Exercise (usually lowers) and Stress (raises) are both present
        # We assume "Exercise" is the one that lowers glucose (negative factor)
        # If activity lowers glucose (< 0) and emotion raises glucose (> 0), ignore emotion.
        
        # --- Peak Window Logic (Hard Override) ---
        last_bolus_mins = 9999
        risk_state = "LOW"
        
        if manual_last_bolus_min is not None:
             last_bolus_mins = manual_last_bolus_min
        else:
            # Find last meaningful dose
            for log in history:
                if log.actual_dose and log.actual_dose > 0.5:
                    delta = (current_time - log.timestamp).total_seconds() / 60
                    if delta >= 0:
                        last_bolus_mins = delta
                        break
        
        is_peak_window = (60 <= last_bolus_mins <= 120)
        
        if activity != "None" and is_peak_window:
            # Danger Zone override
            final_modifier = -0.50
            notes = "⚠️ PEAK RISK: Maximum Safety Reduction (-50%) applied."
            risk_state = "HIGH"
        else:
            # Standard Logic
            if act_mod < 0 and emo_mod > 0:
                final_modifier = act_mod
                notes = "Priority Rule Applied: Ignored emotion stress spike due to exercise."
            else:
                final_modifier = act_mod + emo_mod
                notes = "Standard modifiers applied."
                
            if is_peak_window:
                 # In window but no activity, still alert? User said "AND Activity == True" for the reduction.
                 # But UI status might want to show peak anyway? 
                 # Request says: visual status... State A (During Peak).
                 # Let's set HIGH if in Window, but only reduce if Active?
                 # "Risk of hypoglycemia is tied to Peak Moment... IF Time... AND Activity... THEN Reduce"
                 # "State A (During Peak): Display PEAK ACTION".
                 # So risk state is HIGH (Time based), but reduction is conditional.
                 # Actually, "Exercise Risk: HIGH". So if I am NOT exercising, is the risk high?
                 # Let's stick to: In Window = Peak Action state.
                 risk_state = "HIGH"
            
        adjusted_insulin = gross_insulin * (1 + final_modifier)
        
        
        # 3. IOB Subtraction REMOVED
        # User requested to abandon standard IOB curve.
        final_dose = adjusted_insulin
        
        # Safety floor
        if final_dose < 0:
            final_dose = 0.0
            
        # Rounding suggestion
        # Determine rounding based on total dose size? Usually to nearest 0.5 or 1.0. 
        # Requirement says "advise on rounding logic". Let's round to nearest 0.5 for now.
        recommended_dose = round(final_dose)
        
        return {
            "carb_dose": carb_insulin,
            "correction_dose": correction_insulin,
            "gross_dose": gross_insulin,
            "gross_dose": gross_insulin,
            # "iob": iob, # Removed
            "activity_modifier": act_mod,
            "emotion_modifier": emo_mod,
            "final_modifier_used": final_modifier,
            "adjusted_dose": adjusted_insulin,
            "final_dose_raw": final_dose,
            "recommended_dose": recommended_dose,
            "risk_state": risk_state,
            "notes": notes
        }

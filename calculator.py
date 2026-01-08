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

    def calculate_iob(self, history: List[Log], current_time: datetime) -> float:
        """
        Calculates Insulin On Board (IOB) using a linear decay model.
        """
        iob = 0.0
        duration_minutes = self.settings.duration_of_action * 60
        
        for log in history:
            if not log.actual_dose:
                continue
                
            elapsed_minutes = (current_time - log.timestamp).total_seconds() / 60
            
            if 0 <= elapsed_minutes < duration_minutes:
                # Linear decay: Percentage remaining = (Duration - Elapsed) / Duration
                remaining_percent = (duration_minutes - elapsed_minutes) / duration_minutes
                iob += log.actual_dose * remaining_percent
                
        return max(0.0, iob)

    def calculate_dose(self, 
                       current_glucose: int, 
                       carbs: int, 
                       activity: str, 
                       emotion: str, 
                       history: List[Log]) -> dict:
        
        current_time = datetime.now()
        
        # 1. Base Components
        icr = self.get_icr(current_time)
        carb_insulin = carbs / icr
        
        target = self.settings.target_glucose
        threshold = self.settings.correction_threshold
        
        if current_glucose > threshold:
            correction_insulin = (current_glucose - target) / self.settings.isf
        else:
            correction_insulin = 0.0
        
        gross_insulin = carb_insulin + correction_insulin
        
        # 2. Contextual Modifiers
        modifier_percent = 0.0
        
        # Activity Factors
        activity_factors = {
            "Gym/Weights": 0.10,   # +10%
            "Running": -0.30,      # -30%
            "Swimming": -0.30,     # -30%
            "Yoga": -0.10,         # -10%
            "None": 0.0
        }
        
        # Emotion Factors
        emotion_factors = {
            "Stress": 0.20,    # +20%
            "Anxious": 0.10,   # +10%
            "Calm": 0.0
        }
        
        act_mod = activity_factors.get(activity, 0.0)
        emo_mod = emotion_factors.get(emotion, 0.0)
        
        # Priority Rule: If Exercise (usually lowers) and Stress (raises) are both present
        # We assume "Exercise" is the one that lowers glucose (negative factor)
        # If activity lowers glucose (< 0) and emotion raises glucose (> 0), ignore emotion.
        
        if act_mod < 0 and emo_mod > 0:
            final_modifier = act_mod
            notes = "Priority Rule Applied: Ignored emotion stress spike due to exercise."
        else:
            final_modifier = act_mod + emo_mod
            notes = "Standard modifiers applied."
            
        adjusted_insulin = gross_insulin * (1 + final_modifier)
        
        # 3. IOB Subtraction
        iob = self.calculate_iob(history, current_time)
        final_dose = adjusted_insulin - iob
        
        # Safety floor
        if final_dose < 0:
            final_dose = 0.0
            
        # Rounding suggestion
        # Determine rounding based on total dose size? Usually to nearest 0.5 or 1.0. 
        # Requirement says "advise on rounding logic". Let's round to nearest 0.5 for now.
        recommended_dose = round(final_dose * 2) / 2
        
        return {
            "carb_dose": carb_insulin,
            "correction_dose": correction_insulin,
            "gross_dose": gross_insulin,
            "iob": iob,
            "activity_modifier": act_mod,
            "emotion_modifier": emo_mod,
            "final_modifier_used": final_modifier,
            "adjusted_dose": adjusted_insulin,
            "final_dose_raw": final_dose,
            "recommended_dose": recommended_dose,
            "notes": notes
        }

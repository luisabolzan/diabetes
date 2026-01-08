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
                       duration_minutes: int = 0,
                       intensity: str = "Moderate", # Slow, Moderate, Fast
                       user_weight: float = 70.0,
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
        # These are BASE modifiers for Moderate intensity
        activity_factors = {
            "Gym/Weights": self.settings.mod_gym,
            "Running": self.settings.mod_run,
            "Swimming": self.settings.mod_swim,
            "Beach Tennis": self.settings.mod_beach_tennis,
            "None": 0.0
        }
        
        # Emotion Factors
        emotion_factors = {
            "Stress": self.settings.mod_stress,
            "Anxious": self.settings.mod_anxious,
            "Calm": 0.0
        }
        
        base_act_mod = activity_factors.get(activity, 0.0)
        emo_mod = emotion_factors.get(emotion, 0.0)
        
        # --- METs & Intensity Logic ---
        # Map Activity + Intensity -> METs
        # Default METs (Moderate)
        met_defaults = {
            "Gym/Weights": 5.0,
            "Running": 9.8, 
            "Swimming": 8.0,
            "Beach Tennis": 7.3,
            "None": 1.0
        }
        
        # Intensity Multipliers for METs
        # Slow 0.8x, Moderate 1.0x, Fast 1.25x
        met_mult = 1.0
        if intensity == "Slow": met_mult = 0.8
        elif intensity == "Fast": met_mult = 1.25
        
        base_mets = met_defaults.get(activity, 1.0)
        final_mets = base_mets * met_mult
        
        # Energy Expenditure = METs * Weight(kg) * Time(hours)
        hours = duration_minutes / 60.0
        energy_expended = final_mets * user_weight * hours
        
        # --- Intensity Scaling for Insulin Reduction ---
        # If High Intensity (> 12 METs), increase reduction (1.3x)
        # If Low Intensity (< 6 METs), maybe decrease? Keeping standard for now.
        
        intensity_impact_factor = 1.0
        intensity_note = ""
        
        if final_mets >= 12.0:
            intensity_impact_factor = 1.25 # Increase reduction by 25%
            intensity_note = " (High Intensity: Extra Reduction)"
        
        scaled_base_act_mod = base_act_mod * intensity_impact_factor
        
        # --- Duration Scaling Logic ---
        act_mod = scaled_base_act_mod
        carb_refuel_msg = None
        scaling_note = ""

        if activity != "None" and duration_minutes > 0:
             if duration_minutes < 20:
                 act_mod = scaled_base_act_mod * 0.5
                 scaling_note = f" (Short {duration_minutes}m)"
             elif 20 <= duration_minutes < 50:
                 act_mod = scaled_base_act_mod 
                 scaling_note = f" (Standard)"
             elif 50 <= duration_minutes < 90:
                 act_mod = scaled_base_act_mod * 1.5
                 scaling_note = f" (Long)"
             else: # >= 90
                 potential = scaled_base_act_mod * 1.5
                 # Cap at -0.50 (Max Safe Reduction)
                 if potential < -0.50:
                     act_mod = -0.50
                 else:
                     act_mod = potential
                     
                 scaling_note = f" (Endurance: Capped)"
                 carb_refuel_msg = "Recommendation: Carb Refuel (15-30g) every hour."
        
        # Combine notes
        full_activity_note = f"{intensity_note}{scaling_note}"
        
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
                notes = f"Priority Rule: Ignored emotion.{full_activity_note}"
            else:
                final_modifier = act_mod + emo_mod
                if full_activity_note:
                    notes = f"Standard.{full_activity_note}"
                else:
                    notes = "Standard modifiers applied."
            
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
            "notes": notes,
            "carb_refuel_msg": carb_refuel_msg,
            "energy_expended": int(energy_expended),
            "mets": round(final_mets, 1)
        }

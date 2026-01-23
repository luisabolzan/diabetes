/**
 * InsulinCalculator - JavaScript Port
 * Handles dose calculation, activity modifiers, and risk assessment.
 */

export class InsulinCalculator {
    constructor(settings) {
        this.settings = settings;
    }

    get_icr(currentTime) {
        const hour = currentTime.getHours();
        // 06:00 - 10:59 -> Breakfast
        // 11:00 - 16:59 -> Lunch
        // 17:00 - 23:59 -> Dinner
        // 00:00 - 05:59 -> Snack/Night

        if (hour >= 6 && hour < 11) return this.settings.icr_breakfast;
        if (hour >= 11 && hour < 17) return this.settings.icr_lunch;
        if (hour >= 17 && hour <= 23) return this.settings.icr_dinner;
        return this.settings.icr_snack;
    }

    calculate_activity_modifier(activity, duration_minutes, intensity, user_weight) {
        const activity_factors = {
            "Gym/Weights": this.settings.mod_gym,
            "Running": this.settings.mod_run,
            "Swimming": this.settings.mod_swim,
            "Beach Tennis": this.settings.mod_beach_tennis,
            "None": 0.0
        };

        let base_act_mod = activity_factors[activity] || 0.0;

        // --- METs Logic ---
        const met_defaults = {
            "Gym/Weights": 5.0,
            "Running": 9.8,
            "Swimming": 8.0,
            "Beach Tennis": 8.0,
            "None": 1.0
        };

        let met_mult = 1.0;
        if (intensity === "Slow") met_mult = 0.8;
        else if (intensity === "Fast") met_mult = 1.25;

        let base_mets = met_defaults[activity] || 1.0;
        let final_mets = base_mets * met_mult;

        // Override for Beach Tennis
        if (activity === "Beach Tennis") {
            if (intensity === "Slow") final_mets = 6.0;
            else if (intensity === "Moderate") final_mets = 8.0;
            else if (intensity === "Fast") final_mets = 11.0;
        }

        // Energy Expenditure
        const hours = duration_minutes / 60.0;
        const energy_expended = final_mets * user_weight * hours;

        // --- Intensity Scaling ---
        let intensity_impact_factor = 1.0;
        let intensity_note = "";

        if (activity === "Beach Tennis") {
            base_act_mod *= 1.2; // Terrain
            if (intensity === "Fast") {
                intensity_impact_factor = 1.4;
                intensity_note = " (Singles Match: High Intensity Reduction)";
            } else if (intensity === "Moderate") {
                intensity_note = " (Doubles Match: Sand Terrain)";
            }
        } else {
            if (intensity === "Slow") {
                intensity_impact_factor = 0.8;
                intensity_note = " (Low Intensity: Reduced Impact)";
            } else if (intensity === "Fast") {
                intensity_impact_factor = 1.25;
                intensity_note = " (High Intensity: Extra Reduction)";
            }

            if (final_mets >= 12.0) {
                intensity_impact_factor = Math.max(intensity_impact_factor, 1.4);
                intensity_note = " (Extreme Intensity: Max Reduction)";
            }
        }

        const scaled_base_act_mod = base_act_mod * intensity_impact_factor;

        // --- Duration Scaling ---
        let act_mod = scaled_base_act_mod;
        let carb_refuel_msg = null;
        let scaling_note = "";

        if (activity !== "None" && duration_minutes > 0) {
            if (duration_minutes < 20) {
                act_mod = scaled_base_act_mod * 0.5;
                scaling_note = ` (Short ${duration_minutes}m)`;
            } else if (duration_minutes >= 20 && duration_minutes < 50) {
                act_mod = scaled_base_act_mod;
                scaling_note = " (Standard)";
            } else if (duration_minutes >= 50 && duration_minutes < 90) {
                act_mod = scaled_base_act_mod * 1.5;
                scaling_note = " (Long)";
            } else { // >= 90
                const potential = scaled_base_act_mod * 1.5;
                if (potential < -0.50) act_mod = -0.50;
                else act_mod = potential;

                scaling_note = " (Endurance: Capped)";
                carb_refuel_msg = "Recommendation: Carb Refuel (15-30g) every hour.";
            }
        }

        const full_note = `${intensity_note}${scaling_note}`;

        return {
            modifier: act_mod,
            mets: final_mets,
            kcal: Math.round(energy_expended),
            notes: full_note,
            carb_refuel: carb_refuel_msg
        };
    }

    calculate_dose(current_glucose, carbs, activity, emotion, history, duration_minutes = 0, intensity = "Moderate", user_weight = 70.0, manual_last_bolus_min = null) {
        const currentTime = new Date();

        // 1. Base Components
        const icr = this.get_icr(currentTime);
        const carb_insulin = carbs / icr;

        const target = this.settings.target_glucose;
        const threshold = this.settings.correction_threshold;

        let correction_insulin = 0.0;
        if (current_glucose >= threshold) {
            correction_insulin = (current_glucose - target) / this.settings.isf;
        }

        const gross_insulin = carb_insulin + correction_insulin;

        // 2. Contextual Modifiers
        const emotion_factors = {
            "Stress": this.settings.mod_stress,
            "Anxious": this.settings.mod_anxious,
            "Calm": 0.0
        };
        const emo_mod = emotion_factors[emotion] || 0.0;

        const act_results = this.calculate_activity_modifier(activity, duration_minutes, intensity, user_weight);
        const act_mod = act_results.modifier;

        // --- Peak Window Logic ---
        let last_bolus_mins = 9999;
        let risk_state = "LOW";

        if (manual_last_bolus_min !== null) {
            last_bolus_mins = manual_last_bolus_min;
        } else {
            // Find last meaningful dose from history
            // history is array of logs with timestamp string or Date object
            for (const log of history) {
                if (log.actual_dose > 0.5) {
                    const logTime = new Date(log.timestamp);
                    const diffMs = currentTime - logTime;
                    const diffMins = diffMs / 1000 / 60;
                    if (diffMins >= 0) {
                        last_bolus_mins = diffMins;
                        break;
                    }
                }
            }
        }

        const is_peak_window = (last_bolus_mins >= 60 && last_bolus_mins <= 120);
        let final_modifier = 0.0;
        let notes = "";

        if (activity !== "None" && is_peak_window) {
            final_modifier = -0.50;
            notes = "⚠️ PEAK RISK: Maximum Safety Reduction (-50%) applied.";
            risk_state = "HIGH";
        } else {
            // Priority Rule
            if (act_mod < 0 && emo_mod > 0) {
                final_modifier = act_mod;
                notes = `Priority Rule: Ignored emotion.${act_results.notes}`;
            } else {
                final_modifier = act_mod + emo_mod;
                notes = act_results.notes ? `Standard.${act_results.notes}` : "Standard modifiers applied.";
            }
        }

        let adjusted_insulin = gross_insulin * (1 + final_modifier);

        // Safety floor
        if (adjusted_insulin < 0) adjusted_insulin = 0.0;

        const recommended_dose = Math.round(adjusted_insulin); // Round to nearest integer (No half-units)

        return {
            carb_dose: carb_insulin,
            correction_dose: correction_insulin,
            gross_dose: gross_insulin,
            activity_modifier: act_mod,
            emotion_modifier: emo_mod,
            final_modifier_used: final_modifier,
            adjusted_dose: adjusted_insulin,
            recommended_dose: recommended_dose,
            risk_state: risk_state,
            notes: notes,
            carb_refuel_msg: act_results.carb_refuel,
            energy_expended: act_results.kcal,
            mets: act_results.mets.toFixed(1)
        };
    }
}

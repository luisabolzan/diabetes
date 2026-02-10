from nicegui import ui, run
from src.database import init_db, SessionLocal, Settings, Log, Feedback, Adjustment, Food
from sqlalchemy.orm import joinedload
from src.calculator import InsulinCalculator
from datetime import datetime
import csv
import io
import os
try:
    import torch
    from src.predict import predict_bytes, RGBModel, device
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("WARNING: PyTorch not found. AI features disabled.")
    # Dummy objects to prevent NameError
    predict_bytes = None
    RGBModel = None
    device = None


# Initialize Database
init_db()

def get_settings():
    session = SessionLocal()
    settings = session.query(Settings).first()
    session.close()
    return settings

def save_settings(s_input):
    session = SessionLocal()
    settings = session.query(Settings).first()
    settings.icr_breakfast = float(s_input['icr_breakfast'])
    settings.icr_lunch = float(s_input['icr_lunch'])
    settings.icr_dinner = float(s_input['icr_dinner'])
    settings.icr_snack = float(s_input['icr_snack'])
    settings.isf = float(s_input['isf'])
    settings.target_glucose = int(s_input['target_glucose'])
    settings.correction_threshold = int(s_input['correction_threshold'])
    settings.weight = float(s_input.get('weight', 70.0))
    # Duration removed
    
    # Save Dynamic Modifiers
    settings.mod_gym = float(s_input.get('mod_gym', 0.10))
    settings.mod_run = float(s_input.get('mod_run', -0.30))
    settings.mod_swim = float(s_input.get('mod_swim', -0.30))
    settings.mod_beach_tennis = float(s_input.get('mod_beach_tennis', -0.20))
    settings.mod_stress = float(s_input.get('mod_stress', 0.20))
    settings.mod_anxious = float(s_input.get('mod_anxious', 0.10))
    
    session.commit()
    session.close()
    ui.notify('Settings Saved!', type='positive')

def save_log(log_data):
    session = SessionLocal()
    new_log = Log(**log_data)
    session.add(new_log)
    session.commit()
    session.close()
    ui.notify('Log Saved to History', type='positive')

def get_all_food_options():
    session = SessionLocal()
    foods = session.query(Food).all()
    # Create options for ui.select: dict {value: label}
    options = {}
    for f in foods:
        label = f"{f.name} ({f.measure}) - {f.carbs}g CHO | {f.kcal} Kcal"
        options[f.id] = label
    session.close()
    return options

def get_logs():
    session = SessionLocal()
    logs = session.query(Log).options(joinedload(Log.feedback)).order_by(Log.timestamp.desc()).all()
    session.close()
    return logs

def get_adjustments():
    session = SessionLocal()
    adjs = session.query(Adjustment).options(joinedload(Adjustment.log)).order_by(Adjustment.timestamp.desc()).all()
    session.close()
    return adjs

def run_heuristic_adjustment(session, log, outcome):
    """
    Adjusts settings based on feedback outcome.
    Hypo -> Decrease Factor (more negative for exercise, less positive for stress)
    Hyper -> Increase Factor
    """
    settings = session.query(Settings).first()
    adjustment_made = False
    
    # Map activity/emotion names to Settings columns
    param_map = {
        "Gym/Weights": "mod_gym",
        "Running": "mod_run",
        "Swimming": "mod_swim",
        "Beach Tennis": "mod_beach_tennis",
        "Stress": "mod_stress",
        "Anxious": "mod_anxious"
    }
    
    # Determine direction: Hypo = -0.05, Hyper = +0.05
    delta = 0.0
    if outcome == "Hypo":
        delta = -0.05
    elif outcome == "Hyper":
        delta = 0.05
    else:
        return # Perfect, no change needed
        
    targets = []
    if log.activity and log.activity != "None":
        targets.append(log.activity)
    if log.emotion and log.emotion != "Calm":
        targets.append(log.emotion)
        
    for t in targets:
        col_name = param_map.get(t)
        if col_name:
            old_val = getattr(settings, col_name)
            new_val = old_val + delta
            
            # Update Setting
            setattr(settings, col_name, new_val)
            
            # Create Adjustment Record
            adj = Adjustment(
                ref_log_id=log.id,
                parameter=t,
                old_value=old_val,
                new_value=new_val,
                rationale=f"Auto-adjusted due to {outcome} event.",
                timestamp=datetime.now()
            )
            session.add(adj)
            adjustment_made = True
            
    if adjustment_made:
        ui.notify(f"Algorithm updated settings based on {outcome}!", type='positive', color='deep-purple')

def export_logs():
    logs = get_logs()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Glucose', 'Carbs', 'Activity', 'Emotion', 'Recommended Dose', 'Actual Dose', 'Outcome'])
    
    for l in logs:
        outcome = l.feedback.outcome if l.feedback else ""
        writer.writerow([
            l.timestamp.strftime('%Y-%m-%d %H:%M'),
            l.glucose,
            l.carbs,
            l.activity,
            l.emotion,
            l.recommended_dose,
            l.actual_dose,
            outcome
        ])
    
    # Save to local disk
    local_filename = 'diabetes_logs.csv'
    with open(local_filename, 'w', newline='') as f:
        f.write(output.getvalue())
        
    import os
    abs_path = os.path.abspath(local_filename)
    ui.notify(f'Exported to: {abs_path}', type='positive', close_button=True, timeout=None)
    
    # Also trigger browser download
    ui.download(output.getvalue().encode(), 'diabetes_logs.csv')

def save_feedback(log_id, outcome):
    session = SessionLocal()
    # Check if exists
    fb = session.query(Feedback).filter(Feedback.log_id == log_id).first()
    if not fb:
        fb = Feedback(log_id=log_id)
        session.add(fb)
    
    fb.outcome = outcome
    
    # Run Heuristics
    log = session.query(Log).filter(Log.id == log_id).first()
    if log:
        run_heuristic_adjustment(session, log, outcome)
        
    session.commit()
    session.close()
    ui.notify(f'Feedback "{outcome}" saved!', type='positive')

@ui.page('/')
def main_page():
    # Global Style - Deep Ocean Theme
    ui.add_head_html('''
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <style>
            :root {
                --bg-deep: #0f172a;
                --text-light: #e2e8f0;
                --primary-cyan: #06b6d4;
                --primary-blue: #3b82f6;
                --glass-bg: rgba(30, 41, 59, 0.7);
                --glass-border: rgba(255, 255, 255, 0.1);
            }
            body { 
                background-color: var(--bg-deep); 
                color: var(--text-light);
                font-family: 'Inter', sans-serif;
            }
            .glass-panel {
                background: var(--glass-bg);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid var(--glass-border);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                border-radius: 16px;
            }
            .action-btn {
                background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
                color: white;
                font-weight: 600;
                border: none;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
            }
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(6, 182, 212, 0.6);
            }
            .input-field .q-field__control {
                background: rgba(255, 255, 255, 0.05) !important;
                border-radius: 8px;
            }
            .input-field .q-field__label {
                color: #94a3b8;
            }
            .input-field input, .input-field .q-select__content {
                color: white !important;
            }
            .q-tab {
                color: #94a3b8;
            }
            .q-tab--active {
                color: var(--primary-cyan);
            }
        </style>
    ''')
    
    # Header
    with ui.header().classes('bg-transparent text-white'):
        with ui.row().classes('items-center q-ml-md'):
            ui.label('Diabetes Manager').classes('text-h6 font-bold text-cyan-400')
            ui.label('v2.1 (Texture)').classes('text-xs text-cyan-200 q-ml-sm opacity-60')

    # Tabs
    with ui.tabs().classes('w-full text-grey-400') as tabs:
        calc_tab = ui.tab('Calculator').classes('text-lg')
        insights_tab = ui.tab('Insights').classes('text-lg') 
        history_tab = ui.tab('History').classes('text-lg')
        settings_tab = ui.tab('Settings').classes('text-lg')

    with ui.tab_panels(tabs, value=calc_tab).classes('w-full p-4 bg-transparent animated fadeIn'):
        
        # --- CALCULATOR TAB ---
        with ui.tab_panel(calc_tab):
            with ui.card().classes('w-full max-w-lg mx-auto p-6 glass-panel no-shadow'):
                # --- LIVE STATUS DASHBOARD ---
                status_container = ui.column().classes('w-full items-center justify-center q-mb-lg p-2 bg-black/20 rounded-lg')
                def update_live_status():
                    status_container.clear()
                    try:
                        mins = int(last_dose_input.value)
                    except:
                        mins = 180 # Safe default
                        
                    is_peak = 60 <= mins <= 120
                    with status_container:
                         if is_peak:
                             with ui.row().classes('bg-red-500/20 border border-red-500 rounded-full px-4 py-1 items-center gap-2'):
                                    ui.icon('warning', color='red-400')
                                    ui.label('PEAK ACTION').classes('text-red-400 font-bold')
                             ui.label(f'{mins} min ago - Exercise Risk: HIGH').classes('text-red-300 text-xs q-mt-xs font-bold uppercase tracking-widest')
                         else:
                             with ui.row().classes('bg-green-500/20 border border-green-500 rounded-full px-4 py-1 items-center gap-2'):
                                    ui.icon('check_circle', color='green-400')
                                    ui.label('SAFE TAIL').classes('text-green-400 font-bold')
                             ui.label(f'{mins} min ago - Exercise Risk: LOW').classes('text-green-300 text-xs q-mt-xs font-bold uppercase tracking-widest')

                ui.label('Bolus Calculator').classes('text-h5 q-mb-lg text-cyan-300 font-bold text-center')
                
                with ui.grid(columns=3).classes('w-full gap-4'):
                    glucose_input = ui.number(label='Current Glucose', value=120, format='%.0f').classes('w-full input-field').props('dark filled')
                    carbs_input = ui.number(label='Carbs (g)', value=0, format='%.0f').classes('w-full input-field').props('dark filled')
                    kcal_input = ui.number(label='Calories', value=0, format='%.0f').classes('w-full input-field').props('dark filled')
                
                # Manual Override Input
                last_dose_input = ui.number(label='Time Since Last Dose (min)', value=180, format='%.0f', on_change=lambda: update_live_status()).classes('w-full input-field q-mt-md').props('dark filled')
                # Initialize status
                update_live_status()
                
                # --- MEAL BUILDER ---
                with ui.dialog() as food_dialog, ui.card().classes('w-full max-w-4xl glass-panel p-6'):
                    ui.label('Meal Builder').classes('text-h5 text-cyan-300 font-bold q-mb-md')
                    
                    plate_container = ui.column().classes('w-full bg-black/20 p-4 rounded-lg q-mb-md')
                    plate_items = []
                    
                    def add_to_plate(val):
                        if not val: return
                        
                        food_id = val
                        if isinstance(val, dict) and 'value' in val:
                            food_id = val['value']
                        
                        try:
                            food_id = int(food_id)
                        except (ValueError, TypeError):
                             if hasattr(val, 'get'):
                                 try:
                                     food_id = int(val.get('value'))
                                 except:
                                     return
                             else:
                                 return
                        
                        session = SessionLocal()
                        food_item = session.query(Food).filter(Food.id == food_id).first()
                        
                        if food_item:
                            from types import SimpleNamespace
                            f = SimpleNamespace(name=food_item.name, measure=food_item.measure, carbs=food_item.carbs, kcal=food_item.kcal)
                            plate_items.append(f)
                            update_plate()
                            
                        session.close()
                        food_select.value = None

                    def remove_from_plate(idx):
                        plate_items.pop(idx)
                        update_plate()

                    def update_plate():
                        plate_container.clear()
                        total_carbs = sum(f.carbs for f in plate_items)
                        total_kcal = sum(f.kcal for f in plate_items)
                        with plate_container:
                            ui.label(f'Virtual Plate (Total: {total_carbs:.1f}g CHO | {total_kcal} Kcal)').classes('text-lg text-green-400 font-bold q-mb-sm')
                            with ui.scroll_area().classes('h-32 w-full'):
                                for i, f in enumerate(plate_items):
                                    with ui.row().classes('w-full items-center justify-between q-py-xs border-b border-white/5'):
                                        ui.label(f"{f.name} ({f.measure})").classes('text-sm text-grey-300')
                                        with ui.row().classes('items-center gap-2'):
                                            ui.label(f"{f.carbs}g | {f.kcal} Kcal").classes('text-sm font-bold text-white')
                                            ui.button(icon='delete', on_click=lambda idx=i: remove_from_plate(idx)).props('flat dense round text-color=red-400 size=sm')

                    options = get_all_food_options()
                    
                    with ui.row().classes('w-full items-center gap-2'):
                        food_select = ui.select(
                            options=options, 
                            with_input=True, 
                            label='Search food',
                            on_change=lambda e: add_to_plate(e.value) if e.value else None
                        ).classes('w-full input-field').props('dark filled use-input behavior=menu')

                    def confirm_meal():
                        total_c = sum(f.carbs for f in plate_items)
                        total_k = sum(f.kcal for f in plate_items)
                        carbs_input.value = total_c
                        kcal_input.value = total_k
                        food_dialog.close()
                        ui.notify(f'Filled {total_c}g CHO & {total_k} Kcal!', type='positive')
                        
                    with ui.row().classes('w-full justify-end gap-4'):
                        ui.button('Cancel', on_click=food_dialog.close).props('flat color=grey')
                        ui.button('Use Meal', on_click=confirm_meal).classes('bg-gradient-to-r from-cyan-500 to-blue-500 text-white')
                    
                    update_plate()

                ui.button('Open Meal Builder', icon='restaurant_menu', on_click=food_dialog.open).classes('w-full q-mt-sm bg-purple-900/50 text-purple-200 border border-purple-500/30 hover:bg-purple-800/50').props('flat')
                
                ui.label('Context').classes('text-subtitle1 q-mt-md text-cyan-200 opacity-80')
                with ui.grid(columns=2).classes('gap-4'):
                    activity_select = ui.select(
                        ['None', 'Gym/Weights', 'Running', 'Swimming', 'Beach Tennis'], 
                        label='Activity', value='None'
                    ).classes('w-full mt-0 input-field').props('dark filled behavior=menu')

                    duration_input = ui.number(label='Duration (min)', value=30, format='%.0f').classes('w-full input-field').props('dark filled')
                
                intensity_select = ui.select(
                    ['Slow', 'Moderate', 'Fast'],
                    label='Intensity (Speed/Effort)', value='Moderate'
                ).classes('w-full q-mt-sm input-field').props('dark filled behavior=menu')
                
                emotion_select = ui.select(
                    ['Calm', 'Stress', 'Anxious'], 
                    label='Emotion', value='Calm'
                ).classes('w-full q-mt-sm input-field').props('dark filled behavior=menu')

                result_area = ui.column().classes('w-full q-mt-lg hidden')
                
                def on_calculate():
                    session = SessionLocal()
                    current_settings = session.query(Settings).first()
                    history = session.query(Log).order_by(Log.timestamp.desc()).limit(10).all()
                    session.close()
                    
                    calc = InsulinCalculator(current_settings)
                    
                    try:
                        g = int(glucose_input.value)
                        c = int(carbs_input.value)
                    except:
                        ui.notify('Invalid Input', type='negative', color='red-5')
                        return

                    res = calc.calculate_dose(g, c, activity_select.value, emotion_select.value, history, 
                                              duration_minutes=int(duration_input.value or 0),
                                              intensity=intensity_select.value,
                                              user_weight=current_settings.weight,
                                              manual_last_bolus_min=int(last_dose_input.value))
                    
                    result_area.clear()
                    result_area.classes(remove='hidden')
                    
                    with result_area:
                        ui.separator().classes('bg-cyan-900 opacity-50')
                        
                        risk = res.get('risk_state', 'LOW')
                        if risk == 'HIGH':
                            with ui.row().classes('w-full justify-center q-mt-md'):
                                with ui.row().classes('bg-red-500/20 border border-red-500 rounded-full px-4 py-1 items-center gap-2'):
                                    ui.icon('warning', color='red-400')
                                    ui.label('PEAK ACTION').classes('text-red-400 font-bold')
                            ui.label('Exercise Risk: HIGH').classes('text-center text-red-300 text-xs q-mt-xs font-bold uppercase tracking-widest w-full')
                        else:
                            with ui.row().classes('w-full justify-center q-mt-md'):
                                with ui.row().classes('bg-green-500/20 border border-green-500 rounded-full px-4 py-1 items-center gap-2'):
                                    ui.icon('check_circle', color='green-400')
                                    ui.label('SAFE TAIL').classes('text-green-400 font-bold')
                            ui.label('Exercise Risk: LOW').classes('text-center text-green-300 text-xs q-mt-xs font-bold uppercase tracking-widest w-full')

                        if res.get('energy_expended', 0) > 0:
                            ui.label(f"Est. Burn: ~{res['energy_expended']} Kcal ({res['mets']} METs)").classes('w-full text-center text-xs text-yellow-300 font-bold q-mt-sm')

                        if res.get('carb_refuel_msg'):
                             with ui.row().classes('w-full justify-center q-mt-md'):
                                with ui.row().classes('bg-orange-500/20 border border-orange-500 rounded-lg px-4 py-2 items-center gap-2'):
                                    ui.icon('restaurant', color='orange-400')
                                    ui.label(res['carb_refuel_msg']).classes('text-orange-300 font-bold text-sm')

                        with ui.row().classes('w-full justify-center q-my-md'):
                             ui.label(f"{res['recommended_dose']} units").classes('text-6xl text-cyan-400 font-black drop-shadow-lg')
                        ui.label("Recommended Dose").classes('text-center text-grey-400 text-sm uppercase tracking-widest w-full')
                        
                        with ui.expansion('Calculation Details', icon='info').classes('w-full text-grey-300 q-mt-md input-field rounded-lg').props('dark'):
                            ui.markdown(f"""
                            - **Gross Dose**: {res['gross_dose']:.2f} u
                                - Carbs: {res['carb_dose']:.2f} u
                                - Correction: {res['correction_dose']:.2f} u
                            - **Modifiers**:
                                - Activity: {res['activity_modifier']:.0%}
                                - Emotion: {res['emotion_modifier']:.0%}
                                - *Final Used*: {res['final_modifier_used']:.0%} ({res['notes']})
                            - **Adjusted**: {res['adjusted_dose']:.2f} u
                            """).classes('text-grey-300')
                        
                        log_entry = {
                            "glucose": g,
                            "carbs": c,
                            "activity": activity_select.value,
                            "emotion": emotion_select.value,
                            "recommended_dose": res['recommended_dose'],
                            "actual_dose": res['recommended_dose'], 
                            "timestamp": datetime.now()
                        }
                        
                        ui.button('Save to History', icon='save', on_click=lambda: save_log(log_entry)).classes('w-full q-mt-md bg-cyan-900 text-cyan-100 hover:bg-cyan-800').props('flat')

                ui.button('CALCULATE', on_click=on_calculate).classes('w-full q-mt-xl action-btn py-3 text-lg rounded-xl')
                
                result_area
        
        # --- INSIGHTS TAB ---
        with ui.tab_panel(insights_tab):
            with ui.card().classes('w-full max-w-4xl mx-auto p-6 glass-panel no-shadow h-full'):
                ui.label('Activity Impact Analysis').classes('text-h5 text-cyan-300 font-bold q-mb-md')
                
                with ui.row().classes('w-full items-center gap-4 q-mb-md'):
                     viz_activity = ui.select(
                        ['Running', 'Swimming', 'Beach Tennis', 'Gym/Weights'], 
                        label='Select Activity', value='Running'
                    ).classes('w-64 input-field').props('dark filled behavior=menu')
                
                chart_container = ui.element('div').classes('w-full h-96')
                
                def update_chart():
                     chart_container.clear()
                     act = viz_activity.value
                     if not act: return
                     durations = list(range(0, 130, 10))
                     series_slow = []
                     series_mod = []
                     series_fast = []
                     sim_weight = 70.0 
                     s = get_settings()
                     calc = InsulinCalculator(s)
                     for d in durations:
                         r_slow = calc.calculate_activity_modifier(act, d, "Slow", sim_weight)
                         r_mod = calc.calculate_activity_modifier(act, d, "Moderate", sim_weight)
                         r_fast = calc.calculate_activity_modifier(act, d, "Fast", sim_weight)
                         series_slow.append(round(r_slow['modifier'] * 100, 1))
                         series_mod.append(round(r_mod['modifier'] * 100, 1))
                         series_fast.append(round(r_fast['modifier'] * 100, 1))
                     with chart_container:
                         ui.echart({
                            'tooltip': {'trigger': 'axis'},
                            'legend': {'textStyle': {'color': '#ccc'}},
                            'xAxis': {
                                'type': 'category', 'data': durations, 'name': 'Min',
                                'axisLine': {'lineStyle': {'color': '#ccc'}}
                            },
                            'yAxis': {
                                'type': 'value', 'name': '%',
                                'axisLine': {'lineStyle': {'color': '#ccc'}},
                                'splitLine': {'lineStyle': {'color': '#333'}}
                            },
                            'series': [
                                {'name': 'Slow', 'type': 'line', 'data': series_slow, 'smooth': True, 'itemStyle': {'color': '#4ade80'}},
                                {'name': 'Moderate', 'type': 'line', 'data': series_mod, 'smooth': True, 'itemStyle': {'color': '#fbbf24'}},
                                {'name': 'Fast/High', 'type': 'line', 'data': series_fast, 'smooth': True, 'itemStyle': {'color': '#f87171'}}
                            ],
                            'grid': {'containLabel': True, 'left': '5%', 'right': '5%'}
                         }).classes('w-full h-full')
                
                viz_activity.on_value_change(update_chart)
                update_chart()

        # --- SETTINGS TAB ---
        with ui.tab_panel(settings_tab):
            current_s = get_settings()
            with ui.card().classes('w-full max-w-lg mx-auto p-6 glass-panel no-shadow'):
                ui.label('Configuration').classes('text-h5 q-mb-lg text-cyan-300 font-bold')
                
                s_values = {
                    'icr_breakfast': current_s.icr_breakfast,
                    'icr_lunch': current_s.icr_lunch,
                    'icr_dinner': current_s.icr_dinner,
                    'icr_snack': current_s.icr_snack,
                    'isf': current_s.isf,
                    'target_glucose': current_s.target_glucose,
                    'correction_threshold': current_s.correction_threshold,
                    'weight': current_s.weight,
                    'mod_gym': current_s.mod_gym,
                    'mod_run': current_s.mod_run,
                    'mod_swim': current_s.mod_swim,
                    'mod_beach_tennis': current_s.mod_beach_tennis,
                    'mod_stress': current_s.mod_stress,
                    'mod_anxious': current_s.mod_anxious
                }
                
                ui.label('Insulin-to-Carb Ratios').classes('text-subtitle2 q-mt-sm text-cyan-100')
                with ui.grid(columns=2).classes('gap-4'):
                    ui.number('Breakfast', value=s_values['icr_breakfast'], on_change=lambda e: s_values.update({'icr_breakfast': e.value})).classes('input-field').props('dark filled')
                    ui.number('Lunch', value=s_values['icr_lunch'], on_change=lambda e: s_values.update({'icr_lunch': e.value})).classes('input-field').props('dark filled')
                    ui.number('Dinner', value=s_values['icr_dinner'], on_change=lambda e: s_values.update({'icr_dinner': e.value})).classes('input-field').props('dark filled')
                    ui.number('Snack', value=s_values['icr_snack'], on_change=lambda e: s_values.update({'icr_snack': e.value})).classes('input-field').props('dark filled')

                ui.label('Personal Factors').classes('text-subtitle2 q-mt-lg text-cyan-100')
                ui.number('Weight (kg)', value=s_values.get('weight', 70), on_change=lambda e: s_values.update({'weight': e.value})).classes('w-full input-field').props('dark filled')
                ui.number('ISF', value=s_values['isf'], on_change=lambda e: s_values.update({'isf': e.value})).classes('w-full input-field').props('dark filled')
                ui.number('Target Glucose', value=s_values['target_glucose'], on_change=lambda e: s_values.update({'target_glucose': e.value})).classes('w-full input-field').props('dark filled')
                ui.number('Correction Threshold', value=s_values['correction_threshold'], on_change=lambda e: s_values.update({'correction_threshold': e.value})).classes('w-full input-field').props('dark filled')

                ui.button('Save Settings', on_click=lambda: save_settings(s_values)).classes('w-full q-mt-xl action-btn py-2')

        # --- HISTORY TAB ---
        with ui.tab_panel(history_tab):
            with ui.row().classes('items-center justify-between w-full q-mb-md'):
                 ui.label('History Log').classes('text-h5 text-cyan-300 font-bold')
                 with ui.row().classes('gap-2'):
                    ui.button(icon='refresh', on_click=lambda: refresh_history()).props('flat round dense text-color=cyan-400')
                    ui.button('Export', icon='download', on_click=export_logs).classes('bg-cyan-900 text-cyan-100').props('flat dense')
            
            def refresh_history():
                history_container.clear()
                logs = get_logs()
                if not logs:
                    with history_container:
                         ui.label('No logs found.').classes('text-grey italic text-center w-full q-mt-lg')
                    return
                with history_container:
                    for l in logs:
                        with ui.card().classes('w-full q-mb-md p-4 glass-panel no-shadow border-l-4 border-cyan-500'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(l.timestamp.strftime('%Y-%m-%d %H:%M')).classes('font-bold text-gray-300')
                                ui.label(f"{l.actual_dose} u").classes('text-cyan-400 font-black text-xl')
                            with ui.row().classes('w-full items-center gap-4 text-sm text-gray-400 q-mt-sm'):
                                ui.label(f"Glu: {l.glucose} | Carb: {l.carbs}")
                                ui.label(f"{l.activity} | {l.emotion}")
                            
                            fb_text = l.feedback.outcome if l.feedback else "No Feedback"
                            fb_colors = {'Perfect': 'green-400', 'Hypo': 'red-400', 'Hyper': 'orange-400', 'No Feedback': 'grey-600'}
                            fb_c = fb_colors.get(fb_text, 'grey-600')
                            ui.separator().classes('q-my-sm bg-gray-700')
                            with ui.row().classes('items-center w-full justify-between'):
                                ui.label(f"{fb_text}").classes(f'text-{fb_c} font-bold text-sm')
                                with ui.button(icon='edit').props('flat round size=sm color=cyan-400'):
                                    with ui.menu().props('dark'):
                                        ui.menu_item('Hypo (Low)', on_click=lambda id=l.id: [save_feedback(id, 'Hypo'), refresh_history()])
                                        ui.menu_item('Perfect', on_click=lambda id=l.id: [save_feedback(id, 'Perfect'), refresh_history()])
                                        ui.menu_item('Hyper (High)', on_click=lambda id=l.id: [save_feedback(id, 'Hyper'), refresh_history()])

    # --- SCAN FOOD ---
    if HAS_TORCH:
        try:
            model = RGBModel().to(device)
            # Check if file exists to avoid crash
            if os.path.exists("nutrition5k_model_rgb.pth"):
                model.load_state_dict(torch.load("nutrition5k_model_rgb.pth", map_location=device))
                model.eval()
                print("Model loaded successfully (RGB-Only).")
            else:
                print("Warning: Model file not found.")
                model = None
        except Exception as e:
            print(f"Warning: Model could not be loaded: {e}")
            model = None
    else:
        print("PyTorch not installed. App running in Lite Mode.")
        model = None

    scan_state = {
        'image_bytes': None,
        'uploaded_name': "Captured Image"
    }
    
    # ----------------------------------------------------
    # CRITICAL FIX 1: ASYNC UPLOAD HANDLER
    # ----------------------------------------------------
    async def handle_scan_upload(e):
        try:
            # Fix: Await the read coroutine
            if hasattr(e.file, 'read'):
                 # Check if it's awaitable (coroutine) or standard method
                 # If user says it returns a coroutine, we await it.
                 # In NiceGUI/Starlette, e.content is file-like, e.file is sometimes internal.
                 # But sticking to user instructions:
                 try:
                    image_bytes = await e.file.read()
                 except TypeError:
                    # Fallback if it wasn't actually a coroutine
                    image_bytes = e.file.read()
            else:
                 # Fallback if it's a file path string
                 with open(e.file, 'rb') as f:
                     image_bytes = f.read()

            scan_state['image_bytes'] = image_bytes
            scan_state['uploaded_name'] = "Captured Image"

            scan_status_label.text = "Ready to analyze (Image Captured)"
            scan_status_label.classes(remove='text-grey-400', add='text-green-400 font-bold')
            analyze_btn.enable()
            ui.notify('Image uploaded! Click Analyze.', type='positive')

        except Exception as err:
            print(f"ERROR reading upload: {err}")
            ui.notify(f"Upload Error: {err}", type='negative')

    async def analyze_image():
        if not scan_state['image_bytes'] or not model:
            ui.notify('Error: No image or model not loaded.', type='negative')
            return
        
        # Loading Dialog
        loading_dialog = ui.dialog()
        with loading_dialog, ui.card().classes('w-64 items-center justify-center p-6 glass-panel'):
             ui.spinner(size='lg', color='cyan-400')
             ui.label('Analyzing...').classes('text-cyan-200 q-mt-md animate-pulse')
             
        loading_dialog.open()
        
        # ----------------------------------------------------
        # CRITICAL FIX 2: ROBUST TRY/FINALLY & NON-BLOCKING
        # ----------------------------------------------------
        try:
            # Run in separate thread (IO bound wrapper) to avoid freezing main loop
            # We use io_bound (thread pool) because sharing the 'model' object across processes 
            # (cpu_bound) causes pickling errors with PyTorch.
            pred_carbs = await run.io_bound(predict_bytes, model, scan_state['image_bytes'])
                
            carbs_input.value = round(pred_carbs)
            ui.notify(f"Prediction: {pred_carbs:.1f}g Carbs", type='positive', color='green')
            scan_dialog.close()
            
            scan_state['image_bytes'] = None
            scan_status_label.text = "Waiting for image..."
            scan_status_label.classes(remove='text-green-400 font-bold', add='text-grey-400')
            analyze_btn.disable()
            
        except Exception as e:
            ui.notify(f"Analysis Failed: {e}", type='negative')
            print(f"Error analyzing: {e}")
        finally:
            loading_dialog.close() # Always close the spinner!

    with ui.dialog() as scan_dialog, ui.card().classes('glass-panel p-6 w-full max-w-sm'):
        ui.label('Scan Food').classes('text-h6 text-cyan-300 font-bold q-mb-md text-center')
        
        scan_status_label = ui.label('Waiting for image...').classes('text-center text-xs q-mb-lg text-grey-400')
        
        with ui.column().classes('w-full gap-4'):
            ui.upload(
                label='Take Photo', 
                auto_upload=True,
                on_upload=handle_scan_upload
            ).props('accept="image/*" capture="environment" color=cyan-500 flat bordered class="full-width"')
            
            ui.label('OR').classes('text-center text-xs font-bold text-grey-600')
            
            ui.upload(
                label='Choose from Gallery', 
                auto_upload=True,
                on_upload=handle_scan_upload
            ).props('accept="image/*" color=purple-400 flat bordered class="full-width"')
            
            analyze_btn = ui.button('ANALYZE & COUNT', on_click=analyze_image).classes('w-full bg-gradient-to-r from-green-400 to-cyan-500 text-white font-bold q-mt-md')
            analyze_btn.disable()
            
            ui.button('Cancel', on_click=scan_dialog.close).props('flat color=grey class="full-width q-mt-sm"')

    with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
        ui.button(on_click=scan_dialog.open, icon='photo_camera').props('fab color=cyan-500 push size=lg shadow-lg').tooltip('Scan Food')

if __name__ in {"__main__", "__mp_main__"}:
    # Check if running in Cloud (Render sets PORT env)
    port = int(os.environ.get('PORT', 8080))
    # Disable native mode if in cloud
    is_native = os.environ.get('RENDER', 'False') == 'False'
    
    ui.run(
        title='Diabetes App',
        native=is_native, # True locally, False on Render
        reload=False,
        port=port,
        host='0.0.0.0' # Listen on all interfaces
    )

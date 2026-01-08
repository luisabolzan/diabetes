from nicegui import ui
from database import init_db, SessionLocal, Settings, Log, Feedback, Adjustment, Food
from sqlalchemy.orm import joinedload
from calculator import InsulinCalculator
from datetime import datetime
import csv
import io

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
    settings.correction_threshold = int(s_input['correction_threshold'])
    settings.weight = float(s_input.get('weight', 70.0))
    # Duration removed
    
    # Save Dynamic Modifiers
    settings.mod_gym = float(s_input.get('mod_gym', 0.10))
    settings.mod_run = float(s_input.get('mod_run', -0.30))
    settings.mod_swim = float(s_input.get('mod_swim', -0.30))
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
    # Create options for ui.select: list of dicts {'label': '...', 'value': ...}
    # Create options for ui.select: dict {value: label}
    # This prevents [object Object] display issues in NiceGUI
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
            # simple icon if possible, or just text
            ui.label('Diabetes Manager').classes('text-h6 font-bold text-cyan-400')

    # Tabs
    with ui.tabs().classes('w-full text-grey-400') as tabs:
        calc_tab = ui.tab('Calculator').classes('text-lg')
        insights_tab = ui.tab('Insights').classes('text-lg') 
        # Note: moved Insights content to its own panel below
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
                    glucose_input = ui.number(label='Current Glucose (mg/dL)', value=120, format='%.0f').classes('w-full input-field').props('dark filled')
                    carbs_input = ui.number(label='Carbs (g)', value=0, format='%.0f').classes('w-full input-field').props('dark filled')
                    kcal_input = ui.number(label='Calories (Kcal)', value=0, format='%.0f').classes('w-full input-field').props('dark filled')
                
                # Manual Override Input
                last_dose_input = ui.number(label='Time Since Last Dose (min)', value=180, format='%.0f', on_change=lambda: update_live_status()).classes('w-full input-field q-mt-md').props('dark filled')
                # Initialize status
                update_live_status()
                
                # --- MEAL BUILDER ---
                with ui.dialog() as food_dialog, ui.card().classes('w-full max-w-4xl glass-panel p-6'):
                    ui.label('Meal Builder').classes('text-h5 text-cyan-300 font-bold q-mb-md')
                    
                    
                    # Search replaced by ui.select below
                    
                    results_container = ui.column().classes('w-full h-64 overflow-y-auto q-mb-md p-2 border border-white/10 rounded')
                    
                    plate_container = ui.column().classes('w-full bg-black/20 p-4 rounded-lg q-mb-md')
                    plate_items = []
                    
                    def add_to_plate(val):
                        if not val: return
                        
                        # Handle potential dict input from ui.select
                        food_id = val
                        if isinstance(val, dict) and 'value' in val:
                            food_id = val['value']
                        
                        # Ensure ID is valid (int)
                        try:
                            food_id = int(food_id)
                        except (ValueError, TypeError):
                             # Fallback: if somehow it's still a dict or weird object, try to extract 'value' if possible
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
                            # Create a simple object to hold the data
                            from types import SimpleNamespace
                            f = SimpleNamespace(name=food_item.name, measure=food_item.measure, carbs=food_item.carbs, kcal=food_item.kcal)
                            plate_items.append(f)
                            update_plate()
                            
                        session.close()
                        # Reset selector
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

                    # Load options once
                    options = get_all_food_options()
                    
                    with ui.row().classes('w-full items-center gap-2'):
                        food_select = ui.select(
                            options=options, 
                            with_input=True, 
                            label='Search food (Type to filter)',
                            on_change=lambda e: add_to_plate(e.value) if e.value else None
                        ).classes('w-full input-field').props('dark filled use-input behavior=menu')
                        # Note: use-input enables text filtering in Quasar/NiceGUI

                    # Legacy search UI removed

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
                    
                    # Initial load
                    # Initial load
                    update_plate()

                ui.button('Open Meal Builder', icon='restaurant_menu', on_click=food_dialog.open).classes('w-full q-mt-sm bg-purple-900/50 text-purple-200 border border-purple-500/30 hover:bg-purple-800/50').props('flat')
                # ---------------------
                
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
                    # Load current settings
                    session = SessionLocal()
                    current_settings = session.query(Settings).first()
                    history = session.query(Log).order_by(Log.timestamp.desc()).limit(10).all() # Get recent logs for IOB
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
                        
                        # Risk Status Badge
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

                        # Energy Expenditure
                        if res.get('energy_expended', 0) > 0:
                            ui.label(f"Est. Burn: ~{res['energy_expended']} Kcal ({res['mets']} METs)").classes('w-full text-center text-xs text-yellow-300 font-bold q-mt-sm')

                        # Carb Refuel Warning
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
                        
                        # Prepare log data
                        log_entry = {
                            "glucose": g,
                            "carbs": c,
                            "activity": activity_select.value,
                            "emotion": emotion_select.value,
                            "recommended_dose": res['recommended_dose'],
                            "actual_dose": res['recommended_dose'], # Default to recommended
                            "timestamp": datetime.now()
                        }
                        
                        ui.button('Save to History', icon='save', on_click=lambda: save_log(log_entry)).classes('w-full q-mt-md bg-cyan-900 text-cyan-100 hover:bg-cyan-800').props('flat')

                ui.button('CALCULATE', on_click=on_calculate).classes('w-full q-mt-xl action-btn py-3 text-lg rounded-xl')
                
                result_area
        
        # --- INSIGHTS TAB ---
        with ui.tab_panel(insights_tab):
            with ui.card().classes('w-full max-w-4xl mx-auto p-6 glass-panel no-shadow h-full'):
                ui.label('Activity Impact Analysis').classes('text-h5 text-cyan-300 font-bold q-mb-md')
                ui.label('Visualize how duration and intensity affect insulin reduction.').classes('text-grey-400 q-mb-lg')
                
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
                     
                     durations = list(range(0, 130, 10)) # 0 to 120 min
                     
                     series_slow = []
                     series_mod = []
                     series_fast = []
                     
                     
                     sim_weight = 70.0 
                     
                     # Instantiate calculator for visualization
                     s = get_settings()
                     calc = InsulinCalculator(s)
                     
                     for d in durations:
                         # Calculate for each intensity
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
                                'type': 'category', 
                                'data': durations, 
                                'name': 'Min',
                                'axisLine': {'lineStyle': {'color': '#ccc'}}
                            },
                            'yAxis': {
                                'type': 'value', 
                                'name': '%',
                                'axisLabel': {'formatter': '{value} %'},
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
                
                # We use a dict to hold values for easy saving
                s_values = {
                    'icr_breakfast': current_s.icr_breakfast,
                    'icr_lunch': current_s.icr_lunch,
                    'icr_dinner': current_s.icr_dinner,
                    'icr_snack': current_s.icr_snack,
                    'isf': current_s.isf,
                    'target_glucose': current_s.target_glucose,
                    'correction_threshold': current_s.correction_threshold,
                    'correction_threshold': current_s.correction_threshold,
                    'weight': current_s.weight, # Added weight
                    # 'duration': current_s.duration_of_action, removed
                    # Modifiers
                    'mod_gym': current_s.mod_gym,
                    'mod_run': current_s.mod_run,
                    'mod_swim': current_s.mod_swim,
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
                ui.number('ISF (1u drops X mg/dL)', value=s_values['isf'], on_change=lambda e: s_values.update({'isf': e.value})).classes('w-full input-field').props('dark filled')
                ui.number('Target Glucose (mg/dL)', value=s_values['target_glucose'], on_change=lambda e: s_values.update({'target_glucose': e.value})).classes('w-full input-field').props('dark filled')
                ui.number('Correction Threshold (mg/dL)', value=s_values['correction_threshold'], on_change=lambda e: s_values.update({'correction_threshold': e.value})).classes('w-full input-field').props('dark filled')

                
                ui.label('Adaptive Modifiers (Current)').classes('text-subtitle2 q-mt-lg text-purple-200')
                with ui.grid(columns=2).classes('gap-4'):
                     ui.number('Gym/Weights', value=s_values['mod_gym'], format='%.2f', on_change=lambda e: s_values.update({'mod_gym': e.value})).classes('input-field').props('dark filled')
                     ui.number('Running', value=s_values['mod_run'], format='%.2f', on_change=lambda e: s_values.update({'mod_run': e.value})).classes('input-field').props('dark filled')
                     ui.number('Swimming', value=s_values['mod_swim'], format='%.2f', on_change=lambda e: s_values.update({'mod_swim': e.value})).classes('input-field').props('dark filled')
                     ui.number('Beach Tennis', value=s_values['mod_beach_tennis'], format='%.2f', on_change=lambda e: s_values.update({'mod_beach_tennis': e.value})).classes('input-field').props('dark filled')
                     
                     ui.separator().classes('col-span-2 bg-white/10 q-my-sm')
                     
                     ui.number('Stress', value=s_values['mod_stress'], format='%.2f', on_change=lambda e: s_values.update({'mod_stress': e.value})).classes('input-field').props('dark filled')
                     ui.number('Anxious', value=s_values['mod_anxious'], format='%.2f', on_change=lambda e: s_values.update({'mod_anxious': e.value})).classes('input-field').props('dark filled')
                
                ui.button('Save Settings', on_click=lambda: save_settings(s_values)).classes('w-full q-mt-xl action-btn py-2')

        # --- HISTORY TAB ---
        with ui.tab_panel(history_tab):
            with ui.row().classes('items-center justify-between w-full q-mb-md'):
                 ui.label('History Log').classes('text-h5 text-cyan-300 font-bold')
                 with ui.row().classes('gap-2'):
                    ui.button(icon='refresh', on_click=lambda: refresh_history()).props('flat round dense text-color=cyan-400')
                    ui.button('Export', icon='download', on_click=export_logs).classes('bg-cyan-900 text-cyan-100').props('flat dense')
            
            # Helper to refresh table
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
                            
                            # Feedback Section
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

            history_container = ui.column().classes('w-full max-w-2xl mx-auto')
            refresh_history()

    # Run native
    # ui.run(title='Diabetes App', native=True) is called in logic below if ran as script, 
    # but since we overwrite main.py we rely on standard "main" block.

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Diabetes App', native=True, reload=False) # Reload false for production/native feel

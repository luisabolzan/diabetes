from nicegui import ui
from database import init_db, SessionLocal, Settings, Log, Feedback
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
    settings.duration_of_action = float(s_input['duration'])
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

def get_logs():
    session = SessionLocal()
    logs = session.query(Log).options(joinedload(Log.feedback)).order_by(Log.timestamp.desc()).all()
    session.close()
    return logs

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
    
    ui.download(output.getvalue().encode(), 'diabetes_logs.csv')

def save_feedback(log_id, outcome):
    session = SessionLocal()
    # Check if exists
    fb = session.query(Feedback).filter(Feedback.log_id == log_id).first()
    if not fb:
        fb = Feedback(log_id=log_id)
        session.add(fb)
    
    fb.outcome = outcome
    session.commit()
    session.close()
    ui.notify(f'Feedback "{outcome}" saved!', type='positive')

@ui.page('/')
def main_page():
    # Global Style
    ui.add_head_html('<style>body { background-color: #f0f4f8; }</style>')
    
    # Header
    with ui.header(elevated=True).classes('bg-primary text-white'):
        ui.label('Diabetes Manager').classes('text-h6 q-ml-md')

    # Tabs
    with ui.tabs().classes('w-full') as tabs:
        calc_tab = ui.tab('Calculator')
        settings_tab = ui.tab('Settings')
        history_tab = ui.tab('History')

    with ui.tab_panels(tabs, value=calc_tab).classes('w-full p-4 bg-transparent'):
        
        # --- CALCULATOR TAB ---
        with ui.tab_panel(calc_tab):
            with ui.card().classes('w-full max-w-lg mx-auto p-4'):
                ui.label('Bolus Calculator').classes('text-h5 q-mb-md')
                
                with ui.grid(columns=2).classes('w-full gap-4'):
                    glucose_input = ui.number(label='Current Glucose (mg/dL)', value=120, format='%.0f').classes('w-full')
                    carbs_input = ui.number(label='Carbs (g)', value=0, format='%.0f').classes('w-full')
                
                activity_select = ui.select(
                    ['None', 'Gym/Weights', 'Running', 'Swimming', 'Yoga'], 
                    label='Activity', value='None'
                ).classes('w-full q-mt-md')
                
                emotion_select = ui.select(
                    ['Calm', 'Stress', 'Anxious'], 
                    label='Emotion', value='Calm'
                ).classes('w-full q-mt-md')

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
                        ui.notify('Invalid Input', type='negative')
                        return

                    res = calc.calculate_dose(g, c, activity_select.value, emotion_select.value, history)
                    
                    result_area.clear()
                    result_area.classes(remove='hidden')
                    
                    with result_area:
                        ui.separator()
                        ui.label(f"Recommended Dose: {res['recommended_dose']} units").classes('text-h4 text-primary font-bold q-my-md')
                        
                        with ui.expansion('Calculation Details', icon='info').classes('w-full'):
                            ui.markdown(f"""
                            - **Gross Dose**: {res['gross_dose']:.2f} u
                                - Carbs: {res['carb_dose']:.2f} u
                                - Correction: {res['correction_dose']:.2f} u
                            - **Modifiers**:
                                - Activity: {res['activity_modifier']:.0%}
                                - Emotion: {res['emotion_modifier']:.0%}
                                - *Final Used*: {res['final_modifier_used']:.0%} ({res['notes']})
                            - **Adjusted**: {res['adjusted_dose']:.2f} u
                            - **IOB Subtracted**: -{res['iob']:.2f} u
                            """)
                        
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
                        
                        ui.button('Save to History', icon='save', on_click=lambda: save_log(log_entry)).classes('w-full q-mt-sm bg-accent text-white')

                ui.button('CALCULATE', on_click=on_calculate).classes('w-full q-mt-lg bg-secondary text-white')
                
                result_area
        
        # --- SETTINGS TAB ---
        with ui.tab_panel(settings_tab):
            current_s = get_settings()
            with ui.card().classes('w-full max-w-lg mx-auto p-4'):
                ui.label('User Settings').classes('text-h5 q-mb-md')
                
                # We use a dict to hold values for easy saving
                s_values = {
                    'icr_breakfast': current_s.icr_breakfast,
                    'icr_lunch': current_s.icr_lunch,
                    'icr_dinner': current_s.icr_dinner,
                    'icr_snack': current_s.icr_snack,
                    'isf': current_s.isf,
                    'target_glucose': current_s.target_glucose,
                    'correction_threshold': current_s.correction_threshold,
                    'duration': current_s.duration_of_action
                }
                
                ui.label('Insulin-to-Carb Ratios (1 unit : X g)').classes('text-subtitle2 q-mt-sm text-grey')
                with ui.grid(columns=2).classes('gap-2'):
                    ui.number('Breakfast', value=s_values['icr_breakfast'], on_change=lambda e: s_values.update({'icr_breakfast': e.value}))
                    ui.number('Lunch', value=s_values['icr_lunch'], on_change=lambda e: s_values.update({'icr_lunch': e.value}))
                    ui.number('Dinner', value=s_values['icr_dinner'], on_change=lambda e: s_values.update({'icr_dinner': e.value}))
                    ui.number('Snack', value=s_values['icr_snack'], on_change=lambda e: s_values.update({'icr_snack': e.value}))

                ui.label('Correction Factors').classes('text-subtitle2 q-mt-md text-grey')
                ui.number('ISF (1 unit drops X mg/dL)', value=s_values['isf'], on_change=lambda e: s_values.update({'isf': e.value})).classes('w-full')
                ui.number('Target Glucose (mg/dL)', value=s_values['target_glucose'], on_change=lambda e: s_values.update({'target_glucose': e.value})).classes('w-full')
                ui.number('Correction Threshold (mg/dL)', value=s_values['correction_threshold'], on_change=lambda e: s_values.update({'correction_threshold': e.value})).classes('w-full')
                ui.number('Duration of Action (Hours)', value=s_values['duration'], on_change=lambda e: s_values.update({'duration': e.value})).classes('w-full')
                
                ui.button('Save Settings', on_click=lambda: save_settings(s_values)).classes('w-full q-mt-lg')

        # --- HISTORY TAB ---
        with ui.tab_panel(history_tab):
            ui.label('History Log').classes('text-h5 q-mb-md')
            
            # Helper to refresh table
            def refresh_history():
                history_container.clear()
                logs = get_logs()
                if not logs:
                    with history_container:
                         ui.label('No logs found.').classes('text-grey italic')
                    return
                
                # We need custom rows to add buttons, but ui.table is simpler for now.
                # Let's use a grid or list for more control, or stick to table and use row click?
                # Best way for actions in table: use ui.table and addslot or just iterate?
                # Let's iterate and build a custom list for flexibility.
                
                with history_container:
                    for l in logs:
                        with ui.card().classes('w-full q-mb-sm p-4'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(l.timestamp.strftime('%Y-%m-%d %H:%M')).classes('font-bold')
                                ui.label(f"{l.actual_dose} u").classes('text-primary font-bold text-lg')
                            
                            with ui.row().classes('w-full items-center gap-4 text-sm text-grey-7'):
                                ui.label(f"G:{l.glucose} | C:{l.carbs}")
                                ui.label(f"{l.activity} | {l.emotion}")
                            
                            # Feedback Section
                            fb_text = l.feedback.outcome if l.feedback else "No Feedback"
                            fb_color = 'green' if fb_text == 'Perfect' else 'red' if fb_text in ['Hypo', 'Hyper'] else 'grey'
                            
                            ui.separator().classes('q-my-sm')
                            with ui.row().classes('items-center gap-2'):
                                ui.label(f"Outcome: {fb_text}").classes(f'text-{fb_color}')
                                
                                with ui.button(icon='edit').props('flat round size=sm'):
                                    with ui.menu():
                                        ui.menu_item('Hypo (Low)', on_click=lambda id=l.id: [save_feedback(id, 'Hypo'), refresh_history()])
                                        ui.menu_item('Perfect', on_click=lambda id=l.id: [save_feedback(id, 'Perfect'), refresh_history()])
                                        ui.menu_item('Hyper (High)', on_click=lambda id=l.id: [save_feedback(id, 'Hyper'), refresh_history()])

            history_container = ui.column().classes('w-full')
            refresh_history()
            
            with ui.row().classes('gap-4 q-mt-md'):
                ui.button('Refresh', icon='refresh', on_click=refresh_history)
                ui.button('Export CSV', icon='download', on_click=export_logs).classes('bg-secondary text-white')

    # Run native
    # ui.run(title='Diabetes App', native=True) is called in logic below if ran as script, 
    # but since we overwrite main.py we rely on standard "main" block.

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Diabetes App', native=True, reload=False) # Reload false for production/native feel

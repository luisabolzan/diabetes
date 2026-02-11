from nicegui import ui
from src.auth import register_user

@ui.page('/register')
def register_page():
    # Styles matching main.py / login_page.py
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
                margin: 0;
            }
            .glass-panel {
                background: var(--glass-bg);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid var(--glass-border);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                border-radius: 16px;
            }
            .input-field .q-field__control {
                background: rgba(255, 255, 255, 0.05) !important;
                border-radius: 8px;
            }
            .input-field input {
                color: white !important;
            }
             .input-field .q-field__label {
                color: #94a3b8;
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
        </style>
    ''')

    def try_register():
        e = email_input.value
        p = password_input.value
        cp = confirm_password_input.value
        
        if not e or not p:
            ui.notify('Please fill all fields', type='negative')
            return
            
        if p != cp:
            ui.notify('Passwords do not match', type='negative')
            return
            
        success, msg = register_user(e, p)
        
        if success:
            ui.notify(msg, type='positive', timeout=6000)
            ui.navigate.to('/login')
        else:
            ui.notify(msg, type='negative')

    with ui.column().classes('w-full h-screen items-center justify-center p-4'):
        
        # --- REGISTER CARD ---
        with ui.card().classes('w-full max-w-sm glass-panel p-8 items-center'):
            ui.label('Create Account').classes('text-h5 font-bold text-cyan-400 q-mb-md')
            
            with ui.column().classes('w-full gap-4'):
                email_input = ui.input('Email').classes('w-full input-field').props('dark filled')
                
                password_input = ui.input('Password', password=True, password_toggle_button=True).classes('w-full input-field').props('dark filled')
                confirm_password_input = ui.input('Confirm Password', password=True, password_toggle_button=True).classes('w-full input-field').props('dark filled')
                
                ui.button('REGISTER', on_click=try_register).classes('w-full action-btn q-mt-sm py-3 rounded-lg text-lg')
                
                ui.button('Already have an account? Login', on_click=lambda: ui.navigate.to('/login')).classes('w-full text-cyan-200 text-xs opacity-70 hover:opacity-100').props('flat capitalization=none')

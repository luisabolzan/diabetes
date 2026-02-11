from nicegui import ui, app
from src.auth import login_user, reset_password_email 

@ui.page('/login')
def login_page():
    # If already logged in, redirect to home
    if app.storage.user.get('access_token'):
        ui.navigate.to('/')
        return

    # Styles matching main.py
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

    def try_login():
        success, msg, session_data = login_user(email_input.value, password_input.value)
        if success:
            app.storage.user.update(session_data)
            ui.navigate.to('/')
        else:
            ui.notify(msg, type='negative', color='red-400')

    # --- Forgot Password Logic ---
    def open_forgot_password():
        reset_dialog.open()
        reset_step1.classes(remove='hidden')
        reset_step2.classes(add='hidden')
        reset_email_input.value = ''

    def do_reset_password():
        email = reset_email_input.value
        if not email:
            ui.notify('Email cannot be empty', type='negative')
            return
            
        success, msg = reset_password_email(email)
        if success:
             ui.notify(msg, type='positive')
             reset_dialog.close()
        else:
             ui.notify(msg, type='negative')

    with ui.column().classes('w-full h-screen items-center justify-center p-4'):
        
        # --- LOGIN CARD ---
        with ui.card().classes('w-full max-w-sm glass-panel p-8 items-center'):
            ui.label('Diabetes Manager').classes('text-h5 font-bold text-cyan-400 q-mb-xs')
            ui.label('Login to continue').classes('text-sm text-gray-400 q-mb-lg')
            
            with ui.column().classes('w-full gap-4'):
                email_input = ui.input('Email').classes('w-full input-field').props('dark filled')
                
                password_input = ui.input('Password', password=True, password_toggle_button=True).classes('w-full input-field').props('dark filled')
                password_input.on('keydown.enter', try_login)

                ui.button('LOGIN', on_click=try_login).classes('w-full action-btn q-mt-sm py-3 rounded-lg text-lg')
                
                with ui.row().classes('w-full justify-between items-center q-mt-sm px-2'):
                    ui.button('Create Account', on_click=lambda: ui.navigate.to('/register')).classes('text-cyan-400 text-xs font-bold').props('flat capitalization=none')
                    ui.button('Forgot Password?', on_click=open_forgot_password).classes('text-cyan-200 text-xs opacity-70 hover:opacity-100').props('flat capitalization=none')

    # --- PASSWORD RESET DIALOG ---
    with ui.dialog() as reset_dialog, ui.card().classes('glass-panel p-6 w-full max-w-sm'):
        ui.label('Reset Password').classes('text-h6 text-cyan-300 font-bold q-mb-md')
        
        # STEP 1: Enter Email (Supabase handles valid/invalid internally for security usually, or returns error)
        with ui.column().classes('w-full') as reset_step1:
            ui.label('Enter your registered email:').classes('text-gray-400 text-sm q-mb-sm')
            reset_email_input = ui.input('Email').classes('w-full input-field q-mb-md').props('dark filled')
            with ui.row().classes('w-full justify-end gap-2'):
                 ui.button('Cancel', on_click=reset_dialog.close).props('flat color=grey')
                 ui.button('Send Reset Link', on_click=do_reset_password).classes('bg-cyan-600 text-white')

        # STEP 2: Not used in Supabase Email flow directly (link goes to email)
        with ui.column().classes('w-full hidden') as reset_step2:
             pass 

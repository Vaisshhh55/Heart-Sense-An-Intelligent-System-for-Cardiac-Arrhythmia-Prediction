import os, sys, tkinter as tk
sys.path.insert(0, os.path.join(os.getcwd(), 'CARDIAC_ARRHYTHMIA_UPDATED'))
from UI_Working import CardiacArrhythmiaApp
CardiacArrhythmiaApp.load_models = lambda self: setattr(self, 'model_loaded', False)
CardiacArrhythmiaApp.initialize_explainer = lambda self: None
root = tk.Tk()
root.withdraw()
app = CardiacArrhythmiaApp(root, 'Test')
app.current_user = {'user_id': 'TEST', 'username': 'admin', 'full_name': 'Admin User'}
app.current_user_id = 'TEST'
app.current_role = 'admin'
app.login_frame.destroy()
app.build_main_app()
print('SETTINGS_BUILT', getattr(app, 'settings_built', False))
for fn in ['show_hipaa_status', 'show_fda_status', 'show_audit_log', 'show_database_info']:
    print('CALL', fn)
    getattr(app, fn)()
    print(fn + ' OK')
root.destroy()

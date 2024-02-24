import threading
import app
from control_panel import ControlPanel


if __name__ == "__main__":
    control_panel = ControlPanel(run_window_manager=True, fullscreen=True)
    
    app.control_panel = control_panel
    flask_thread = threading.Thread(target=app.run_flask_app)
    flask_thread.start()
    
    control_panel.window_manager.run()
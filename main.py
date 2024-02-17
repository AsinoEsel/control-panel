import threading
import app
from control_panel import ControlPanel


if __name__ == "__main__":
    control_panel = ControlPanel(display_flags=0) # pg.FULLSCREEN
    
    app.control_panel = control_panel
    flask_thread = threading.Thread(target=app.run_flask_app)
    flask_thread.start()
    
    control_panel.window_manager.run()
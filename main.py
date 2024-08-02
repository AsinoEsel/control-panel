import threading
from control_panel import ControlPanel


if __name__ == "__main__":
    control_panel = ControlPanel(fullscreen=True, use_shaders=True, maintain_aspect_ratio=True)
        
    window_manager_thread = threading.Thread(target=control_panel.window_manager.run)
    window_manager_thread.run()
        
    print("END OF MAIN!")
    
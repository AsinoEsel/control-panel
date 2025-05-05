from controlpanel.scripts import ControlAPI
from gui.window_manager import WindowManager
from gui.window_manager.window_manager_setup import *
from gui.widgets import *


def set_up_desktops():
    window_manager: WindowManager | None = ControlAPI.get_game("Window Manager")
    if not window_manager:
        raise ValueError()

    desktop = window_manager.create_new_desktop("main", make_selected=True)
    desktop.add_element(
        terminal := Terminal("Terminal", desktop, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP,
                             h=RENDER_HEIGHT - 2 * DEFAULT_GAP))
    desktop.add_element(
        log := Log("Log", desktop, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP,
                   h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP))
    # empty_widget = Widget("Empty", desktop, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP,
    #                       w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP)
    image = Image("Image", desktop, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP,
                  w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP,
                  image_path=os.path.join(os.path.dirname(__file__), "gui", "media", "robot36.png"))
    desktop.add_element(image)
    text_field = TextField("TextField", desktop, x=RENDER_WIDTH // 2 + DEFAULT_GAP, y=RENDER_HEIGHT // 2 + DEFAULT_GAP,
                           w=RENDER_WIDTH // 2 - 2 * DEFAULT_GAP, h=RENDER_HEIGHT // 2 - 2 * DEFAULT_GAP,
                           text=os.path.join(os.path.dirname(__file__), "gui", "media", "roboter_ascii.txt"), load_ascii_file=True,
                           transparent=False, font=SMALL_FONT)
    # desktop.add_element(STLRenderer(desktop, os.path.join('gui', 'media', 'fox_centered.stl'), x=RENDER_WIDTH//2+DEFAULT_GAP, y=RENDER_HEIGHT//2+DEFAULT_GAP,
    #                            w=RENDER_WIDTH//2-2*DEFAULT_GAP, h=RENDER_HEIGHT//2-2*DEFAULT_GAP))
    # desktop.add_element(Window(desktop, "Hallo", 300, 200, "JP", 200, 300))
    desktop.terminal = terminal
    # desktop.add_element(Taskbar(desktop, 20))
    log.print_to_log("NEUER TEXT", (255, 0, 0))

    desktop2 = window_manager.create_new_desktop("radar")
    desktop2.add_element(Radar("Radar", desktop2, png=os.path.join(os.path.dirname(__file__), "gui", "media", "red_dot_image.png")))

    desktop3 = window_manager.create_new_desktop("movinghead")
    desktop3.add_element(LaserGame("LaserGame", desktop3))

    desktop4 = window_manager.create_new_desktop("controlpanelsimulation")
    desktop4.add_element(ControlPanelSimulation("ControlPanelSimulation", desktop4, ControlAPI.artnet))

    desktop5 = window_manager.create_new_desktop("bliss")
    desktop5.add_element(bliss := Image("Image", desktop5, 0, 0, "controlpanel/scripts/gui/media/bliss.jpg"))
    bliss.do_render_border = False


set_up_desktops()

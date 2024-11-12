from controlpanel.scripts.gui import utils
from .window_manager_setup import *
import time
from controlpanel.shaders import Shaders
from .event_queue import EventQueue
from controlpanel.scripts.gui.widgets import Desktop
from controlpanel.game_manager import BaseGame


class WindowManager(BaseGame):
    def __init__(self):
        super().__init__(name="Window Manager", resolution=RENDER_SIZE)
        self.desktops: dict[str: Desktop] = dict()
        self.desktop: Desktop | None = None
        self.event_queue = EventQueue()
        self.tick = 0

    def create_new_desktop(self, name: str, *, make_selected: bool = False) -> Desktop:
        if self.desktops.get(name) is not None:
            raise ValueError(f"Cannot create desktop: desktop with name {name} already exists!")
        new_desktop = Desktop(name)
        self.desktops[name] = new_desktop
        if make_selected:
            self.desktop = new_desktop
        return new_desktop

    def handle_events(self, events: list[pg.event.Event]) -> None:
        if not self.desktop:
            return
        for event in events:
            if event.type == pg.KEYDOWN and pg.key.get_mods() & pg.KMOD_CTRL and pg.K_0 <= event.key <= pg.K_9:
                self.change_desktop(event.key - pg.K_0 - 1)
                continue
            self.desktop.handle_event(event)

    def update(self, dt: int) -> None:
        if not self.desktop:
            return
        self.tick += 1
        self.desktop.propagate_update(self.tick, dt=dt, joysticks=dict())

    def render(self) -> None:
        if not self.desktop:
            return
        self.screen.blit(self.desktop.surface, (0, 0))

    @staticmethod
    def get_flags(fullscreen: bool, use_shaders: bool) -> int:
        flags = pg.FULLSCREEN if fullscreen else 0
        if use_shaders:
            flags |= pg.OPENGL | pg.DOUBLEBUF
        return flags

    @staticmethod
    def get_output_size(fullscreen: bool, stretch_to_fit: bool) -> tuple[int, int]:
        if not fullscreen:
            return RENDER_SIZE
        if fullscreen and not stretch_to_fit:
            return utils.scale_resolution(RENDER_SIZE, (pg.display.Info().current_w, pg.display.Info().current_h))
        elif fullscreen and stretch_to_fit:
            return pg.display.Info().current_w, pg.display.Info().current_h

    @staticmethod
    def get_scaling_ratio(fullscreen: bool) -> tuple[float, float] | None:
        if fullscreen:
            window_width, window_height = pg.display.get_window_size()
            return RENDER_WIDTH/window_width, RENDER_HEIGHT/window_height
        else:
            return None

    def change_desktop(self, name_or_index: str | int):
        if isinstance(name_or_index, str):
            desktop = self.desktops.get(name_or_index)
        elif isinstance(name_or_index, int):
            if 0 <= name_or_index < len(self.desktops):
                desktop = list(self.desktops.values())[name_or_index]
            else:
                print(f"Desktop #{name_or_index+1} does not exist.")
                return
        else:
            raise ValueError("arg needs to be of type str or int")
        if desktop is not None and desktop is not self.desktop:
            from controlpanel.scripts import ControlAPI
            ControlAPI.fire_event(self.__class__.__name__, "ChangeDesktop", desktop.name)
            self.desktop = desktop

    def run(self, is_fullscreen: bool, use_shaders: bool, stretch_to_fit: bool):
        if self.desktop is None:
            if self.desktops:
                self.desktop = list(self.desktops.values())[0]
            else:
                self.desktop = Desktop("Empty")

        pg.init()
        screen = pg.display.set_mode(size=self.get_output_size(is_fullscreen, stretch_to_fit),
                                     flags=self.get_flags(is_fullscreen, use_shaders))
        clock = pg.time.Clock()

        joysticks: dict[int:pg.joystick.JoystickType] = dict()
        
        if use_shaders:
            shaders = Shaders(texture_sizes=[RENDER_SIZE, QUARTER_RENDER_SIZE, QUARTER_RENDER_SIZE],
                              shader_operations=[(1, "Downscale", {"_MainTex": 0}),
                                                 (1, "Threshold", {"_MainTex": 1}),
                                                 (1, "Blur_H", {"_MainTex": 1}),
                                                 (1, "Blur_V", {"_MainTex": 1}),
                                                 (2, "Ghost", {"_MainTex": 1, "_SecondaryTex": 2}),
                                                 (0, "Add", {"_MainTex": 0, "_SecondaryTex": 2}),
                                                 (0, "CRT", {"_MainTex": 0}),
                                                 (-1, "To_BGRA", {"_MainTex": 0}),
                                                 ])
        else:
            shaders = None
        
        scaling_ratio = self.get_scaling_ratio(is_fullscreen)

        tick = 0
        dt = 0
        while True:
            tick += 1
            current_time = time.time()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                if event.type == pg.JOYDEVICEADDED:
                    joy = pg.joystick.Joystick(event.device_index)
                    joysticks[joy.get_instance_id()] = joy
                    print(f"Joystick {joy.get_instance_id()} connected")
                if pg.key.get_mods() & pg.KMOD_CTRL and event.type == pg.KEYDOWN and pg.K_0 <= event.key <= pg.K_9:
                    self.change_desktop(event.key - pg.K_0 - 1)
                    continue
                if scaling_ratio and event.type in (pg.MOUSEMOTION, pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
                    event.pos = (event.pos[0] * scaling_ratio[0], event.pos[1] * scaling_ratio[1])
                    if event.type == pg.MOUSEMOTION:
                        event.rel = (event.rel[0] * scaling_ratio[0], event.rel[1] * scaling_ratio[1])
                self.desktop.handle_event(event)

            self.event_queue.update()
            self.desktop.propagate_update(tick, dt=dt, joysticks=joysticks)

            if shaders:
                shaders.apply([self.desktop.surface,], current_time)
            else:
                if is_fullscreen:
                    pg.transform.scale(self.desktop.surface, pg.display.get_window_size(), screen)
                else:
                    screen.blit(self.desktop.surface, (0, 0))
            
            pg.event.pump()
            pg.display.flip()
            dt = clock.tick(TARGET_FRAME_RATE)


def main():
    import threading
    run_fullscreen, use_shaders, stretch_to_fit = False, True, False
    window_manager = WindowManager()
    window_manager_thread = threading.Thread(target=window_manager.run,
                                             args=(run_fullscreen, use_shaders, stretch_to_fit))
    window_manager_thread.run()


if __name__ == "__main__":
    main()

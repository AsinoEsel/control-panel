import contextlib
with contextlib.redirect_stdout(None):
    import pygame  # This gets rid of the pygame "support prompt" on import
from threading import Thread
from controlpanel.event_manager import EventManager
from controlpanel.game_manager import GameManager
from controlpanel.scripts import load_scripts, ControlAPI
from controlpanel.micropython_sdk.device_manifest import get_instantiated_devices
from controlpanel.dmx import DMXUniverse, device_list
from artnet import ArtNet
import argparse


def main():
    parser = argparse.ArgumentParser(description='Control Panel')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--no-gui', action='store_true', help='Disable the GUI (enabled by default)')
    group.add_argument('-w', '--windowed', action='store_true', help='Run in windowed mode (fullscreen is default)')
    parser.add_argument('--height', type=int, default=540, help='Height of the game window')
    parser.add_argument('--width', type=int, default=960, help='Width of the game window')
    parser.add_argument('--no-shaders', action='store_true', help='Disable shaders (shaders are enabled by default)')
    group.add_argument('--stretch-to-fit', action='store_true', help='Stretch game to fit screen (black bars by default)')
    parser.add_argument('--load-scripts', nargs='*', help='Load script files (in gui/scripts), all by default. Alternatively, supply the filenames of the script files (or presets) to load. A preset is a .txt file containing newline-separated script file names')
    parser.add_argument('--cheats', '-c', action='store_true', default=False, help='Enable cheat-protected console commands (disabled by default)')
    args, unknown_args = parser.parse_known_args()

    artnet = ArtNet()

    event_manager = EventManager(artnet)

    # window_manager = WindowManager() if not args.no_gui else None
    game_manager = GameManager(resolution=(args.width, args.height),
                               dev_args=unknown_args,
                               is_fullscreen=not args.windowed,
                               use_shaders=not args.no_shaders,
                               stretch_to_fit=args.stretch_to_fit,
                               enable_cheats=args.cheats,
                               )

    ControlAPI.artnet = artnet
    ControlAPI.event_manager = event_manager
    ControlAPI.devices = get_instantiated_devices(ControlAPI.artnet)
    ControlAPI.game_manager = game_manager
    try:
        ControlAPI.dmx = DMXUniverse(None, devices=device_list, target_frequency=10)
    except ConnectionError as err:
        print(err)
    except ValueError as err:
        print('Unable to initiate DMX Universe because of value error.')  # occurred on macOS
        print(err)

    if args.load_scripts is not None:
        load_scripts(args.load_scripts)

    if game_manager is not None:
        game_manager_thread = Thread(target=game_manager.run, daemon=True)
        game_manager_thread.run()
    else:
        pygame.quit()

    event_manager_thread = Thread(target=artnet.listen, args=(None,), daemon=False)

    event_manager_thread.start()
    event_manager_thread.join()


if __name__ == "__main__":
    main()

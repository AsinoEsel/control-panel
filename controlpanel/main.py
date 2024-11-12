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
    parser.add_argument('--no-gui', action='store_true', help='Disable the GUI (enabled by default)')
    group.add_argument('-w', '--windowed', action='store_true', help='Run in windowed mode (fullscreen is default)')
    parser.add_argument('--no-shaders', action='store_true', help='Disable shaders (shaders are enabled by default)')
    group.add_argument('--stretch-to-fit', action='store_true', help='Stretch game to fit screen (black bars by default)')
    parser.add_argument('--load-scripts', nargs='*', help='Load script files (in gui/scripts), all by default. Alternatively, supply the filenames of the script files (or presets) to load. A preset is a .txt file containing newline-separated script file names')
    args = parser.parse_args()

    threads = []

    artnet = ArtNet()

    event_manager = EventManager(artnet)
    event_manager_thread = Thread(target=artnet.listen, args=(None,), daemon=True)
    event_manager_thread.start()
    threads.append(event_manager_thread)

    # window_manager = WindowManager() if not args.no_gui else None
    game_manager = GameManager((960, 540), not args.windowed, not args.no_shaders, args.stretch_to_fit)

    ControlAPI.artnet = artnet
    ControlAPI.event_manager = event_manager
    ControlAPI.devices = get_instantiated_devices(ControlAPI.artnet)
    ControlAPI.game_manager = game_manager
    try:
        ControlAPI.dmx = DMXUniverse(None, devices=device_list, target_frequency=10)
    except ConnectionError:
        print("Unable to initiate DMX Universe because of missing USB to DMX device.")
    except ValueError as err:
        print('Unable to initiate DMX Universe because of value error.')
        print(err)

    if args.load_scripts is not None:
        load_scripts(args.load_scripts)

    if game_manager is not None:
        window_manager_thread = Thread(target=game_manager.run)
        window_manager_thread.run()
        threads.append(window_manager_thread)

    for th in threads:
        th.join()


if __name__ == "__main__":
    main()

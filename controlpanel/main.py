from threading import Thread
from controlpanel.game_manager import GameManager
from controlpanel.scripts import load_scripts, ControlAPI
from controlpanel.dmx import DMXUniverse, device_list
import argparse


def main():
    parser = argparse.ArgumentParser(description='Control Panel')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--no-gui', action='store_true',
                       help='Disable the GUI (enabled by default)')
    group.add_argument('-w', '--windowed', action='store_true',
                       help='Run in windowed mode (fullscreen is default)')
    parser.add_argument('--height', type=int, default=540,
                        help='Height of the game window')
    parser.add_argument('--width', type=int, default=960,
                        help='Width of the game window')
    parser.add_argument('--no-shaders', action='store_true',
                        help='Disable shaders (shaders are enabled by default)')
    group.add_argument('--stretch-to-fit', action='store_true',
                       help='Stretch game to fit screen (black bars by default)')
    parser.add_argument('--load-scripts', nargs='*',
                        help='Load script files (in gui/scripts), all by default. '
                             'Alternatively, supply the filenames of the script files (or presets) to load.'
                             'A preset is a .txt file containing newline-separated script file names')
    parser.add_argument('--no-artnet', action='store_true',
                        help='Disable artnet support, disabling the event manager.')
    parser.add_argument('--cheats', '-c', action='store_true', default=False,
                        help='Enable cheat-protected console commands (disabled by default)')
    args, unknown_args = parser.parse_known_args()

    try:
        from artnet import ArtNet
        failed_to_import_artnet: bool = False
    except ImportError:
        failed_to_import_artnet: bool = True

    if not args.no_artnet and not failed_to_import_artnet:
        from controlpanel.event_manager.event_manager import EventManager
        artnet = ArtNet()  # This is where we initialise our one and ONLY ArtNet instance for the entire program.
        event_manager = EventManager(artnet)
    else:
        artnet = event_manager = None

    ControlAPI.artnet = artnet
    ControlAPI.event_manager = event_manager
    if ControlAPI.event_manager is not None:
        from controlpanel.event_manager import device_getter
        device_getter.devices = event_manager.devices

    game_manager = GameManager(resolution=(args.width, args.height),
                               dev_args=unknown_args,
                               is_fullscreen=not args.windowed,
                               use_shaders=not args.no_shaders,
                               stretch_to_fit=args.stretch_to_fit,
                               enable_cheats=args.cheats,
                               )

    ControlAPI.game_manager = game_manager
    try:
        ControlAPI.dmx = DMXUniverse(None, devices=device_list, target_frequency=10)
    except ValueError as err:
        print('Unable to initiate DMX Universe because of value error.')  # occurred on macOS
        print(err)

    if args.no_artnet:
        print('Running with --no-artnet, event manager was not initialized.')
    elif failed_to_import_artnet:
        print('Failed to import artnet. Event manager was not initialized.')

    if not args.no_artnet and not failed_to_import_artnet:
        artnet_thread = Thread(target=artnet.listen, args=(None,), daemon=True)
        artnet_thread.start()

    if args.load_scripts is not None:
        load_scripts(args.load_scripts)

    game_manager_thread = Thread(target=game_manager.run, daemon=False)
    game_manager_thread.run()


if __name__ == "__main__":
    main()

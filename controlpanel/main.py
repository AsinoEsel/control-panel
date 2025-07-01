from threading import Thread
from artnet import ArtNet
from controlpanel.game_manager import GameManager
from controlpanel.dmx import DMXUniverse, device_list
from controlpanel import api
import argparse


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description='Control Panel')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--no-gui', action='store_true',
                       help='Disable the GUI (enabled by default)')
    group.add_argument('-f', '--fullscreen', action='store_true',
                       help='Run in fullscreen mode (windowed is default)')
    parser.add_argument('--height', type=int, default=540,
                        help='Height of the game window')
    parser.add_argument('--width', type=int, default=960,
                        help='Width of the game window')
    parser.add_argument('--shaders', action='store_true',
                        help='Enable shaders (shaders are disabled by default)')
    group.add_argument('--stretch-to-fit', action='store_true',
                       help='Stretch game to fit screen (black bars by default)')
    parser.add_argument('--load-scripts', nargs='*',
                        help='Load script files (in controlpanel/scripts), all by default. '
                             'Alternatively, supply the filenames of the script files (or presets) to load.'
                             'A preset is a .txt file containing newline-separated script file names')
    parser.add_argument('--cheats', '-c', action='store_true', default=False,
                        help='Enable cheat-protected console commands (disabled by default)')
    return parser.parse_known_args()


def main():
    args, unknown_args = parse_args()

    artnet = ArtNet()  # This is where we initialise our one and ONLY ArtNet instance for the entire program.
    api.Services.artnet = artnet

    event_manager = api.EventManager(artnet)
    api.Services.event_manager = event_manager
    # needs to be called after Services.event_manager has been set
    event_manager.instantiate_devices([api.dummy,])

    game_manager = GameManager(resolution=(args.width, args.height),
                               dev_args=unknown_args,
                               is_fullscreen=args.fullscreen,
                               use_shaders=args.shaders,
                               stretch_to_fit=args.stretch_to_fit,
                               enable_cheats=args.cheats,
                               )
    api.Services.game_manager = game_manager

    try:
        api.Services.dmx = DMXUniverse(None, devices=device_list, target_frequency=10)
    except ValueError as err:
        print('Unable to initiate DMX Universe because of value error.')  # occurred on macOS
        print(err)

    if args.load_scripts is not None:
        api.load_scripts(args.load_scripts)

    game_manager_thread = Thread(target=game_manager.run, daemon=False)
    game_manager_thread.run()


if __name__ == "__main__":
    main()

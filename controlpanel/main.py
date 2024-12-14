from threading import Thread
from controlpanel.event_manager import EventManager
from controlpanel.shared.base import Fixture, Sensor
from controlpanel.gui.window_manager import WindowManager
from controlpanel.scripts import load_scripts, ControlAPI
from controlpanel.shared.device_manifest import get_instantiated_devices
from controlpanel.dmx import DMXUniverse, device_list
from artnet import ArtNet
import argparse


def main():
    parser = argparse.ArgumentParser(description='Control Panel')
    parser.add_argument('--no-gui', action='store_true', help='Disable the GUI (enabled by default)')
    parser.add_argument('-w', '--windowed', action='store_true', help='Run in windowed mode (fullscreen is default)')
    parser.add_argument('--no-shaders', action='store_true', help='Disable shaders (shaders are enabled by default)')
    parser.add_argument('--stretch-to-fit', action='store_true', help='Stretch game to fit screen (black bars by default)')
    parser.add_argument('--load-scripts', nargs='*', help='Load script files (in gui/scripts), all by default. Alternatively, supply the filenames of the script files (or presets) to load. A preset is a .txt file containing newline-separated script file names')
    args = parser.parse_args()

    threads = []

    artnet = ArtNet()

    event_manager = EventManager(artnet)
    event_manager_thread = Thread(target=artnet.listen, args=(None,), daemon=True)
    event_manager_thread.start()
    threads.append(event_manager_thread)

    window_manager = WindowManager() if not args.no_gui else None

    ControlAPI.artnet = artnet
    ControlAPI.event_manager = event_manager
    ControlAPI.devices = get_instantiated_devices(artnet)
    for device in ControlAPI.devices:
        if isinstance(device, Fixture):
            ControlAPI.subscribe(lambda event: device.parse_dmx_data(event.data), "DMX", device.universe, None)
        if isinstance(device, Sensor):
            ControlAPI.subscribe(lambda event: device.parse_trigger_data(event.data), device.name, None, None)
    ControlAPI.window_manager = window_manager
    try:
        ControlAPI.dmx = DMXUniverse(None, devices=device_list, target_frequency=10)
    except ConnectionError:
        print("Unable to initiate DMX Universe because of missing USB to DMX device.")
    except ValueError as err:
        print('Unable to initiate DMX Universe because of value error.')
        print(err)

    if args.load_scripts is not None:
        load_scripts(args.load_scripts)

    if window_manager is not None:
        window_manager_thread = Thread(target=window_manager.run, args=(not args.windowed, not args.no_shaders, args.stretch_to_fit))
        window_manager_thread.run()
        threads.append(window_manager_thread)

    for th in threads:
        th.join()


if __name__ == "__main__":
    main()

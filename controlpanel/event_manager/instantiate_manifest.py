from typing import Any, TYPE_CHECKING
from controlpanel.shared.base import Device, Fixture
import controlpanel.event_manager.dummy as dummylib
import json
import importlib.resources
import io
if TYPE_CHECKING:
    from artnet import ArtNet


def load_file_stream(file_name: str, package: str = 'controlpanel.shared') -> io.BytesIO:
    """
    Loads a font file from a package and returns a BytesIO stream suitable for pygame.font.Font.

    :param file_name: The name of the file (e.g., "my_font.ttf").
    :param package: The dotted path to the package containing the file.
    :return: BytesIO object containing the font data.
    """
    with importlib.resources.open_binary(package, file_name) as file:
        return io.BytesIO(file.read())


JSON_FILENAME = 'device_manifest.json'
manifest = json.load(load_file_stream(JSON_FILENAME))

START_UNIVERSE = 5000

ESPNameType = str
DeviceNameType = str
DeviceKwargsType = dict[str:Any]
DeviceManifestType = dict[str: Device]


def get_instantiated_devices(artnet: "ArtNet") -> DeviceManifestType:
    auto_assign_universes = False
    instanciated_devices = dict()
    universe = START_UNIVERSE
    for esp_name, devices in manifest.items():
        for (cls_name, params) in devices:
            cls = getattr(dummylib, "Dummy" + cls_name)
            if cls is None:
                print(cls_name)
            if issubclass(cls, Fixture):
                if auto_assign_universes and params.get("universe") is None:
                    params["universe"] = universe
                    print(f"Assigned universe {universe} to {params.get("name", "<UNKNOWN>")}.")
                    universe += 1
            filtered_params = {key: value for key, value in params.items() if key in cls.__init__.__code__.co_varnames}
            real_device = cls(artnet=artnet, **filtered_params)
            instanciated_devices[real_device.name] = real_device
    return instanciated_devices

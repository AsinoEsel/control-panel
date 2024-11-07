from typing import Any
from controlpanel.micropython_sdk.devices.base import Fixture, Sensor
import controlpanel.micropython_sdk.devices.dummy as dummylib
from artnet import ArtNet

ESPNameType = str
DeviceNameType = str
DeviceKwargsType = dict[str:Any]
DeviceManifestType = dict[str: Fixture | Sensor]


START_UNIVERSE = 5000


esp_name_manifest = {
    "A0:B7:65:DC:09:28": "ladestation",
    "CC:DB:A7:6A:13:FC": "pilz",
    "": "kommunikation",  # 3C:E9:0E:8C:26:24 kaputt
    "A0:DD:6C:0E:6F:B4": "kuehlwasser",
    "": "bvgpanel",  # 08:D1:F9:E0:B5:A4 kaputt
    "08:D1:F9:E0:D8:E8": "mainframe",
    "08:D1:F9:E1:F6:94": "waehlscheibe",
    "08:D1:F9:E2:9D:DC": "chronometer",
    "08:D1:F9:E0:1A:D0": "biesenthuer",

    # "EC:62:60:93:7F:B8": "test",
    # 08:D1:F9:F8:6D:38 Tobis micro usb (unused)
}


esp_device_manifest: dict[ESPNameType: list[tuple[DeviceNameType, DeviceKwargsType]]] = {
    "bvgpanel": [("BVGPanel", {"name": "TestBVGPanel"}),
                 ("LEDStrip", {"name": "BatterySlotBVG-LEDStrip", "length": 30}),
                 ("Button", {"name": "BatteryButton", "pin": 13}),
                 ("Button", {"name": "AuthorizationKeyBVG", "pin": 12}),
                 ],
    "pilz": [("PWM", {"name": "UVStrobe", "intensity": 1.0}),
             ("LEDStrip", {"name": "PilzLEDs", "length": 5}),
             ("RFIDReader", {"name": "PilzRFID"})
             ],
    "chronometer": [("PWM", {"name": "Chronometer"}),
                    ("LEDStrip", {"name": "ChronometerLampen", "length": 3}),
                    ],
    "waehlscheibe": [("SipoShiftRegister", {"name": "RedYellowLEDs"}),
                     ("SevenSegmentDisplay", {"name": "Display1"}),
                     ("SevenSegmentDisplay", {"name": "Display2"}),
                     ],
    "kommunikation": [],
    "kuehlwasser": [("LEDStrip", {"name": "StatusLEDs", "length": 3}),
                    ("PWM", {"name": "WarnLED"}),
                    ("PWM", {"name": "WaterPressure"}),
                    ("PWM", {"name": "Temperature"}),
                    ],
    "ladestation": [("PWM", {"name": "Voltmeter1"}),
                    ("PWM", {"name": "Voltmeter2"}),
                    ("PWM", {"name": "Voltmeter3"}),
                    ("PWM", {"name": "Voltmeter4"}),
                    ("PWM", {"name": "Batterie"}),
                    ("LEDStrip", {"name": "BatterySlotLadestation-LEDStrip", "length": 30}),
                    ],
}


def get_instantiated_devices(artnet: ArtNet) -> DeviceManifestType:
    auto_assign_universes = False
    instanciated_devices = dict()
    universe = START_UNIVERSE
    for esp_name, devices in esp_device_manifest.items():
        for (cls_name, params) in devices:
            cls = getattr(dummylib, "Dummy" + cls_name)
            if cls is None:
                print(cls_name)
            if issubclass(cls, Fixture):
                if auto_assign_universes and params.get("universe") is None:
                    params["universe"] = universe
                    print(f"Assigned universe {universe} to {params.get("name", "<UNKNOWN>")}.")
                    universe += 1
            # if esp_name != my_esp_name:
            #     continue
            filtered_params = {key: value for key, value in params.items() if key in cls.__init__.__code__.co_varnames}
            real_device = cls(artnet=artnet, **filtered_params)
            instanciated_devices[real_device.name] = real_device
    return instanciated_devices

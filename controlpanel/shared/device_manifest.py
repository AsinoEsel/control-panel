from typing import Any
from controlpanel.shared.base import Fixture, Sensor
import controlpanel.event_manager.dummy as dummylib
from artnet import ArtNet

ESPNameType = str
DeviceNameType = str
DeviceKwargsType = dict[str:Any]
DeviceManifestType = dict[str: Fixture | Sensor]


START_UNIVERSE = 5000


esp_device_manifest: dict[ESPNameType: list[tuple[DeviceNameType, DeviceKwargsType]]] = {
    "bvgpanel": [("BVGPanel", {"name": "TestBVGPanel"}),
                 ("LEDStrip", {"name": "BatterySlotBVG-LEDStrip", "length": 30}),
                 ("Button", {"name": "BatteryButton", "pin": 13}),
                 ("Button", {"name": "AuthorizationKeyBVG", "pin": 12}),
                 ],
    "chronometer": [("PWM", {"name": "Chronometer"}),
                    ("LEDStrip", {"name": "ChronometerLampen", "length": 3}),
                    ("Button", {"name": "BigRedButton"}),
                    ],
    "kommunikation": [("Button", {"name": "ButtonRed"}),
                      ("Button", {"name": "ButtonGreen"}),
                      ("Button", {"name": "ButtonBlue"}),
                      ("Button", {"name": "ButtonPower"}),
                      ],
    "kuehlwasser": [("LEDStrip", {"name": "StatusLEDs", "length": 3}),
                    ("PWM", {"name": "WarnLED"}),
                    ("PWM", {"name": "WaterPressure"}),
                    ("PWM", {"name": "Temperature"}),
                    ("WaterSensor", {"name": "WaterFlowSensor"}),
                    ],
    "ladestation": [("PWM", {"name": "Voltmeter1"}),
                    ("PWM", {"name": "Voltmeter2"}),
                    ("PWM", {"name": "Voltmeter3"}),
                    ("PWM", {"name": "Voltmeter4"}),
                    ("PWM", {"name": "Batterie"}),
                    ("LEDStrip", {"name": "BatterySlotLadestation-LEDStrip", "length": 30}),
                    ("Button", {"name": "AuthorizationKeyCharge"}),
                    ("Button", {"name": "BatteryButtonLadestation"}),
                    ("Button", {"name": "SwitchPos1"}),
                    ("Button", {"name": "SwitchPos2"}),
                    ],
    "mainframe": [("PisoShiftRegister", {"name": "MainframeKeys", "count": 30}),
                  ("LEDStrip", {"name": "MainframeLEDs", "length": 15*16}),
                  ],
    "pilz": [("PWM", {"name": "UVStrobe", "intensity": 1.0}),
             ("LEDStrip", {"name": "PilzLEDs", "length": 5}),
             # ("RFIDReader", {"name": "PilzRFID"}),
             ("BananaPlugs", {"name": "BananaPlugs", "plug_count": 4}),
             ],
    "waehlscheibe": [("SipoShiftRegister", {"name": "RedYellowLEDs"}),
                     ("SevenSegmentDisplay", {"name": "SevenSegmentDisplay", "digits": 16}),
                     ("RotaryDial", {"name": "RotaryDial"}),
                     ("Button", {"name": "PowerSwitch"}),
                     ("Button", {"name": "DialReset"}),
                     ("LEDStrip", {"name": "StatusLED", "length": 1}),
                     # ("RFIDReader", {"name": "RFIDLogin"}),
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

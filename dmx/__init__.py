from .dmx import DMXUniverse, DMXDevice, get_device_url
from .dmx_devices import VaritecColorsStarbar12, MovingHead

dmx_universe = DMXUniverse(url=get_device_url(), devices=[MovingHead("Laser Cockpit", 1),
                                                          MovingHead("Laser Lichthaus", 15),
                                                          VaritecColorsStarbar12("Starbar Cockpit", 300),
                                                          ])

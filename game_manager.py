from artnet import ArtNet, OpCode

def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    if ip not in ESP_DICTIONARY.values():
        return
    print(f"From {IP_DICTIONARY.get(ip)}: {reply}")
    
    
    
    
my_artnet = ArtNet()
my_artnet.subscribe_all(artnet_callback)

import time

ESP_DICTIONARY = {
    "ladestation": "2.0.0.131", # nicht fest?
    "pilz": "2.0.24.45", # FEST
    "wartung": "2.0.24.44", # FEST
    # "mainframe": "2.0.24.16",
    "waehlscheibe": "2.0.24.13", # FEST
    # "terminal": "2.0.0.206",
    "chronometer": "2.0.0.207", # FEST
    "kommunikation": "2.0.0.235", # an Kevin geschickt
    "kuehlwasser": "2.0.0.157", # an Kevin geschickt
    "bvgpanel": "2.0.0.210", # an Kevin geschickt
    "raetselpilz": "2.0.24.17", # nicht fest
}

IP_DICTIONARY = dict((v, k) for k, v in ESP_DICTIONARY.items())


class ESP:
    def __init__(self, name: str, ip: str):
        self.name = name
        self.ip = ip


class GameManager:
    def __init__(self) -> None:
        self.esps = [ESP(name, ip) for name, ip in ESP_DICTIONARY.items()]
    
    def run(self):
        while True:
            time.sleep(10)
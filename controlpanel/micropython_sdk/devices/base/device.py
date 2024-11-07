class Device:
    KEY = 76

    def __init__(self, artnet, name: str):
        self.artnet = artnet
        self.name = name

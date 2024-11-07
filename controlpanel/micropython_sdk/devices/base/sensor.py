from .device import Device


class Sensor(Device):
    SUBKEY = 255

    def __init__(self, artnet, name: str, *, callback=None):
        super().__init__(artnet, name)
        self.callback = callback if callback is not None else self.send_data
        
    def send_data(self, *args, name: str | None = None, subkey: int | None = None, payload: bytes | None = None):
        if name is None:
            name = self.name
        if subkey is None:
            subkey = self.SUBKEY
        if payload is None:
            payload = self.get_payload()
        data = name.encode('ascii') + b'\x00' + payload
        print(f"Sending Trigger with subkey {subkey} and data {data}")
        self.artnet.send_trigger(key=Device.KEY, subkey=subkey, data=data)
    
    def get_payload(self) -> bytes:
        return b""

    def parse_trigger_data(self, data: bytes):
        raise NotImplementedError("Needs to be implemented by subclass!")

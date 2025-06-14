from controlpanel.shared.base import Device


class ESP32:
    def __init__(self, name: str, mac: str, status: str | None = None) -> None:
        self.name: str = name
        self.mac: str = mac
        self.ip: str | None = None
        self.status: str | None = status
        self.devices: dict[str, Device] = {}
        self.subsequent_missed_replies: int = 0

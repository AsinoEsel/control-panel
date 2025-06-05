from controlpanel.shared.compatibility import const


class BaseWaterFlowSensor:
    DEFAULT_POLLING_RATE_HZ: float = const(1.0)

    def __init__(self, polling_rate_hz: float = DEFAULT_POLLING_RATE_HZ):
        self._polling_time_seconds: float = 1 / polling_rate_hz

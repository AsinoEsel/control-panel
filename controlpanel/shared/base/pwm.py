from controlpanel.shared.compatibility import abstractmethod


class BasePWM:
    DEFAULT_UPDATE_RATE_HZ: float = 1.0

    @abstractmethod
    def set_intensity(self, intensity: float) -> None:
        pass

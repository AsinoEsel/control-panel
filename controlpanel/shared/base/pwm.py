from controlpanel.shared.compatibility import abstractmethod


class BasePWM:
    @abstractmethod
    def set_intensity(self, intensity: float) -> None:
        pass

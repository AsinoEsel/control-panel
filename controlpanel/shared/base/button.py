from controlpanel.shared.compatibility import abstractmethod


class BaseButton:
    @abstractmethod
    def get_pressed(self) -> bool:
        pass

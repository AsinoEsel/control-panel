import json
from pathlib import Path
import importlib.util
from . import DEVICE_MANIFEST_PATH


STUB_PATH = Path(importlib.util.find_spec("controlpanel.api").origin).parent / "get_device.pyi"


def generate_get_device_stub_file() -> None:
    with open(DEVICE_MANIFEST_PATH, "r") as f:
        data = json.load(f)

    seen_names = set()
    overloads = []
    device_names = []

    for namespace, devices in data.items():
        for class_name, kwargs in devices:
            name = kwargs.get("name")
            if not name:
                continue
            if name in seen_names:
                raise ValueError(f"Duplicate device name found: {name}")
            seen_names.add(name)

            overloads.append(
                f'@overload\ndef get_device(device_name: Literal["{name}"]) -> {class_name}: ...'
            )
            device_names.append(name)

    # Final combined file content
    boilerplate = """from typing import overload, Literal
from controlpanel.shared.base import Device
from controlpanel.event_manager.dummy import *


"""

    footer = f"""
def get_device(device_name: str) -> Device: ...
"""

    full_code = boilerplate + "\n".join(overloads) + footer

    Path(STUB_PATH).write_text(full_code)


if __name__ == "__main__":
    generate_get_device_stub_file()

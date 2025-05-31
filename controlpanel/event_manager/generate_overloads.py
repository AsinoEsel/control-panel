import json
from pathlib import Path


def generate_device_overloads(json_path: Path, output_path: Path) -> None:
    with open(json_path, "r") as f:
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

    # Create the ValidDeviceNames alias
    sorted_names = sorted(device_names)
    valid_names_literal = ", ".join(f'"{name}"' for name in sorted_names)
    type_alias = f"ValidDeviceNames = Literal[{valid_names_literal}]"

    # Final combined file content
    boilerplate = """from typing import overload, Literal
from controlpanel.shared.base import Device
from .dummy import *


"""

    footer = f"""


{type_alias}


devices: dict[str, Device] = dict()


def get_device(device_name: ValidDeviceNames) -> Device:
    return devices.get(device_name)
"""

    full_code = boilerplate + "\n".join(overloads) + footer

    Path(output_path).write_text(full_code)


def main():
    generate_device_overloads(Path(__file__).parent / '..' / 'shared' / 'device_manifest.json', Path(__file__).parent / "device_getter.py")


if __name__ == "__main__":
    main()

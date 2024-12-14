import subprocess
import argparse
import os


FIRMWARE_FILENAME = "ESP32_GENERIC-20231227-v1.22.0.bin"


def erase_flash(port: str) -> subprocess.CompletedProcess:
    print('Erasing flash...')
    executable = (
        [
            "esptool",
            "--chip",
            "esp32",
            "--port",
            f"{port}",
            "erase_flash",
        ]
    )
    return subprocess.run(executable)


def flash_firmware(file_path: str, port: str) -> subprocess.CompletedProcess:
    print(f'Flashing firmware {file_path}...')
    executable = (
        [
            "esptool",
            "--chip",
            "esp32",
            "--port",
            f"{port}",
            "--baud",
            "460800",
            "write_flash",
            "-z",
            "0x1000",
            file_path,
        ]
    )
    return subprocess.run(executable)


def main():
    parser = argparse.ArgumentParser(description='Control Panel GUI')
    parser.add_argument("--port", type=str, help='The port where the chip is plugged in', required=True)
    parser.add_argument("--firmware", type=str, help='The relative path to the firmware')
    args = parser.parse_args()

    port = args.port
    firmware = args.firmware if args.firmware is not None else os.path.join(os.path.dirname(__file__), FIRMWARE_FILENAME)

    erase_flash(port)
    flash_firmware(firmware, port)


if __name__ == "__main__":
    main()

import subprocess
import argparse
from .checksumtest import file_has_changed, update_checksum
from artnet import ArtNet
import fnmatch
import os
from pathlib import Path

RELATIVE_PATH_TO_IGNORE = '.webreplignore'

script_dir = Path(__file__).resolve().parent
path_to_ignore = script_dir / RELATIVE_PATH_TO_IGNORE


def read_ignore_patterns(filename: Path) -> list[str]:
    """Read ignore patterns from the ignore file."""
    if not filename.exists():
        return []
    with open(filename, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return patterns


def should_ignore(rel_path: str, patterns: list[str]) -> bool:
    """Return True if the given path matches any ignore pattern."""
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


# Load patterns
IGNORE_PATTERNS = read_ignore_patterns(path_to_ignore)
ALWAYS_IGNORE = [str(path_to_ignore), f"{Path(__file__).name}"]
IGNORE_PATTERNS.extend(ALWAYS_IGNORE)


def send_all_files(esp_name: str, ip: str, password: str, directory: Path, *,
                   give_up_on_failed_attempt: bool = False,
                   ignore_checksums: bool = False):
    print(f'Sending ALL files in {directory} to ESP "{esp_name}" @ {ip}')
    successful_transfers = []
    failed_transfers = []

    directory = Path(directory).resolve()
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        rel_root = root_path.relative_to(directory)

        # Skip unwanted root folders
        if ("venv" in root_path.parts) or (not {"upy", "shared"} & set(root_path.parts)):
            continue

        # Filter subdirs
        dirs[:] = [d for d in dirs if not should_ignore(str(rel_root / d), IGNORE_PATTERNS)]

        for file in files:
            rel_path = rel_root / file
            rel_path_str = str(rel_path)

            if should_ignore(rel_path_str, IGNORE_PATTERNS):
                continue

            if not ignore_checksums and not file_has_changed(str(rel_path), esp_name):
                continue

            new_file_path = None
            if file.startswith("main_") and file != f"main_{esp_name}.py":
                continue
            elif file == f"main_{esp_name}.py":
                new_file_path = "main.py"

            if file in ("boot.py", "main.py", "credentials.json", "utils.py", "hostname_manifest.json"):
                new_file_path = file

            result = send_file(esp_name, ip, password, str(rel_path), new_file_path)

            if not result.stderr:
                print(f"Successfully sent {rel_path} to {esp_name}")
                successful_transfers.append(str(rel_path))
                update_checksum(str(rel_path), esp_name)
            else:
                print(result.stderr)
                failed_transfers.append(str(rel_path))
                if give_up_on_failed_attempt:
                    return successful_transfers, failed_transfers

    return successful_transfers, failed_transfers


def get_wifi_ssid():
    try:
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, encoding='cp850', check=True)
        for line in result.stdout.split("\n"):
            if "SSID" in line:
                ssid = line.split(":")[1].strip()
                encoded = ssid.encode('ISO-8859-1')
                decoded = encoded.decode('UTF-8')
                return decoded
        return None
    except FileNotFoundError:
        return None


ACCESS_POINT_IP = "192.168.4.1"
PASSWORD = "incubator"  # password used in webrepl setup
PATH_TO_WEBREPL = Path(__file__).resolve().parent / "webrepl_cli.py"


def send_file(esp_name: str, ip: str, password: str, file_path: str, new_file_path: str|None = None) -> subprocess.CompletedProcess:
    if new_file_path is None:
        new_file_path = file_path.replace("/", "\\")

    # assert "/" not in file_path, "Make sure to replace '/' with '\\' to make webrepl happy."

    print(f'Sending file {file_path} to {esp_name} at {ip}{f" as {new_file_path}" if new_file_path else ""}...')
    executable = (
        [
            "python",
            PATH_TO_WEBREPL,
            "-p",
            password,
            file_path,
            f"{ip}:/{new_file_path if new_file_path else ""}",
        ]
    )
    return subprocess.run(executable, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def flash_esp(esp_name: str, ip: str, password: str, ignore_checksums: bool, give_up_on_failed_attempt: bool):
    successful_transfers, failed_transfers = send_all_files(esp_name, ip, password, Path.cwd(), give_up_on_failed_attempt=give_up_on_failed_attempt, ignore_checksums=ignore_checksums)
    if not successful_transfers and not failed_transfers:
        print(f"{esp_name} appears to be up to date.")
    elif not failed_transfers:
        print(f"Sucessfully transferred all files to {esp_name}")
    elif not successful_transfers:
        print(f"Failed to transfer any files to {esp_name} (Aborted)")
    else:
        print(f"Failed to transfer some files to {esp_name}")
    artnet = ArtNet(ip)
    artnet.send_command(b"RESET")


def transfer():
    parser = argparse.ArgumentParser(description='Control Panel File Transfer Tool')
    parser.add_argument("hostname", help="The IP or hostname of the device to send the files to.")
    parser.add_argument("--IP", help="IP override")
    parser.add_argument("paths", nargs="*", help="Optional: the files to transfer. Default is all in CWD.")
    parser.add_argument('-f', '--force', action='store_true', help='Ignore the checksums.')
    parser.add_argument('-p', '--password', default=PASSWORD, help='The webrepl password.')
    parser.add_argument("--give-up-on-failed-attempt", action='store_true', help="Stop transferring files if a single file failed to transfer.")
    args = parser.parse_args()

    if args.IP is not None:
        ip = args.IP
    else:
        print("Getting ip... ", end="", flush=True)
        import socket
        try:
            ip = socket.gethostbyname(args.hostname)
            print(f"IP is {ip}")
        except socket.gaierror:
            print(f"Hostname {args.hostname} could not be resolved.")
            return

    flash_esp(args.hostname, ip, args.password, args.force, args.give_up_on_failed_attempt)


if __name__ == "__main__":
    transfer()

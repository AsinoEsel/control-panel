import subprocess
import argparse
import os
from pathlib import Path
from .ignore_patterns import IGNORE_PATTERNS, should_ignore
from .checksumtest import file_has_changed, update_checksum
from artnet import ArtNet


script_dir = os.path.dirname(os.path.abspath(__file__))
last_espname_storage_path = os.path.join(script_dir, "last_esp.txt")


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
PATH_TO_WEBREPL = os.path.join(os.path.dirname(script_dir), "webrepl", "webrepl_cli.py")


def send_file(esp_name: str, ip: str, password: str, file_path: str, new_file_path: str|None = None) -> subprocess.CompletedProcess:
    assert "/" not in file_path, "Make sure to replace '/' with '\\' to make webrepl happy."

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


def send_all_files(esp_name: str, ip: str, password: str, directory: str | Path, *,
                   give_up_on_failed_attempt: bool = False,
                   ignore_checksums: bool = False):
    print(f'Sending ALL files in {directory} to ESP "{esp_name}" @ {ip}')
    successful_transfers = []
    failed_transfers = []

    for root, dirs, files in os.walk(directory):
        if (not "upy" in root and not "shared" in root) or "venv" in root:
            continue
        dirs[:] = [d for d in dirs if not should_ignore(d, IGNORE_PATTERNS)]
        for file in files:
            path = os.path.join(os.path.relpath(root, os.getcwd()), file)
            path = path.lstrip("./\\")
            if should_ignore(file, IGNORE_PATTERNS):
                continue
            if not file_has_changed(path, esp_name) and not ignore_checksums:
                continue
                        
            new_file_path = None
            if file.startswith("main_"):
                if file != f"main_{esp_name}.py":
                    # print(f"Skipping {path}, not meant for us!")
                    continue
                else:
                    new_file_path = "main.py"
            root_files = ("boot.py", "boot.py.backup", "credentials.py", "utils.py")
            for root_file in root_files:
                if file == root_file:
                    new_file_path = root_file

            result = send_file(esp_name, ip, password, path, new_file_path)
            if not result.stderr:
                print(f"Sucessfully sent {path} to {esp_name}")
                # print(result.stdout)
                successful_transfers.append(path)
                update_checksum(path, esp_name)
            else:
                print(result.stderr)
                failed_transfers.append(path)
                if give_up_on_failed_attempt:
                    return successful_transfers, failed_transfers
    return successful_transfers, failed_transfers


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
        print("Getting ip... ")
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

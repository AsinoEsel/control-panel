import subprocess
import sys
from .ignore_patterns import IGNORE_PATTERNS, should_ignore
import os
from .checksumtest import file_has_changed, update_checksum
try:
    from .ip_manifest import IP_MANIFEST
except ImportError:
    IP_MANIFEST = dict()
from controlpanel.micropython_sdk.credentials import AP_SSID


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


def send_file(esp_name: str, ip: str, file_path: str, new_file_path: str|None = None) -> subprocess.CompletedProcess:
    assert "/" not in file_path, "Make sure to replace '/' with '\\' to make webrepl happy."

    print(f'Sending file {file_path} to {esp_name} at {ip}{f" as {new_file_path}" if new_file_path else ""}...')
    executable = (
        [
            "python",
            PATH_TO_WEBREPL,
            "-p",
            PASSWORD,
            file_path,
            f"{ip}:/{new_file_path if new_file_path else ""}",
        ]
    )
    return subprocess.run(executable, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def send_all_files(esp_name: str, ip: str, directory: str = os.path.dirname(script_dir), give_up_on_failed_attempt: bool = False):
    print(f'Sending ALL files in {directory} to ESP "{esp_name}" @ {ip}')
    successful_transfers = []
    failed_transfers = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not should_ignore(d, IGNORE_PATTERNS)]
        for file in files:
            # path = os.path.relpath(os.path.join(root, file), directory)
            path = os.path.join(os.path.relpath(root, os.getcwd()), file)
            path = path.lstrip("./\\")
            if should_ignore(file, IGNORE_PATTERNS):
                continue
            if not file_has_changed(path, esp_name):
                continue
                        
            new_file_path = None
            if path.startswith("main_"):
                if path != f"main_{esp_name}.py":
                    # print(f"Skipping {path}, not meant for us!")
                    continue
                else:
                    new_file_path = "main.py"
            
            result = send_file(esp_name, ip, path, new_file_path)
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


def flash_esp(esp_name: str):
    print(f"Attempting to send files to {esp_name}")

    esp = IP_MANIFEST.get(esp_name, None)
    if esp is None:
        raise ValueError(f"Specified esp {esp_name} does not exist in IP manifest.")

    ssid = get_wifi_ssid()
    if ssid is None:
        raise ConnectionError("Not connected to any network or otherwise cannot determine SSID")

    ip = esp.get(ssid, None) if not ssid == AP_SSID else "192.168.4.1"
    if ip is None:
        raise ValueError(f"IP of esp {esp_name} for current network {ssid} does not exist in IP manifest.")

    with open(last_espname_storage_path, "w+") as file:
        file.write(esp_name)
    successful_transfers, failed_transfers = send_all_files(esp_name, ip, give_up_on_failed_attempt=False)
    if not successful_transfers and not failed_transfers:
        print(f"{esp_name} appears to be up to date.")
    elif not failed_transfers:
        print(f"Sucessfully transferred all files to {esp_name}")
    elif not successful_transfers:
        print(f"Failed to transfer any files to {esp_name} (Aborted)")
    else:
        print(f"Failed to transfer some files to {esp_name}")


def transfer():
    if len(sys.argv) == 1:
        if get_wifi_ssid() == AP_SSID:
            send_all_files("accesspoint", ACCESS_POINT_IP)
        else:
            try:
                with open(last_espname_storage_path, "r") as file:
                    esp_name = file.read()
                send_all_files(esp_name, IP_MANIFEST.get(esp_name).get(get_wifi_ssid()))
            except FileNotFoundError:
                print("error")
    elif len(sys.argv) == 2 and sys.argv[1] == "all":
        for esp_name in IP_MANIFEST.keys():
            flash_esp(esp_name)
    elif len(sys.argv) >= 2:
        for esp_name in sys.argv[1:]:
            flash_esp(esp_name)


if __name__ == "__main__":
    transfer()

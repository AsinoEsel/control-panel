import network
import machine


FALLBACK_AP_PASSWORD = "micropython"
CREDENTIALS = "credentials.json"
HOSTNAME_MANIFEST = "hostname_manifest.json"
MAC_ADDRESS: str | None = None
LOCAL_IP: str | None = None


def get_mac_address() -> str:
    if not MAC_ADDRESS:
        raise Exception("MAC_ADDRESS has not yet been determined")
    return MAC_ADDRESS


def _set_mac_address(raw_mac_address: bytes) -> None:
    from binascii import hexlify
    global MAC_ADDRESS
    MAC_ADDRESS = hexlify(raw_mac_address, ':').decode().upper()


def set_hostname(hostname: str) -> None:
    data = load_json(HOSTNAME_MANIFEST) or dict()
    data[get_mac_address()] = hostname
    dump_json(HOSTNAME_MANIFEST, data)


def get_hostname() -> str:
    data: dict = load_json(HOSTNAME_MANIFEST) or dict()
    mac_address: str = get_mac_address()
    hostname: str = data.get(mac_address)
    return hostname or "ESP-" + mac_address.replace(":", "")[-4:]


def create_ap(config: dict[str, str | int] | None = None) -> network.WLAN:
    print("Attempting to create AP...")
    data = load_json(CREDENTIALS) or dict()
    access_point_config = config or data.get("access_point", {})
    ssid, password, authmode = (
            access_point_config.get("ssid") or get_hostname(),
            access_point_config.get("password") or FALLBACK_AP_PASSWORD,
            access_point_config.get("authmode") or 3,
    )

    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid=ssid, password=password, authmode=authmode)
    _set_mac_address(ap_if.config("mac"))
    _set_local_ip(ap_if.ifconfig()[0])
    print('Successfully created an AP with SSID:', ssid)
    return ap_if


def create_modules():
    import os
    print("Attempting to create modules...")

    modules: list[str] = []
    overwritten_files: int = 0

    for filepath in os.listdir():  # TODO "entry" better name than "filepath"?
        if "\\" not in filepath:
            continue

        *folders, filename = filepath.split("\\")

        with open(filepath, 'r') as source_file:
            data = source_file.read()

        os.remove(filepath)

        for i, folder in enumerate(folders):
            try:
                os.mkdir(folder)
                module = "/".join(folders[:i + 1])
                print(f"Creating {"sub" * i}module {module}...")
                modules.append(module)
            except OSError:
                pass
            os.chdir(folder)

        with open(filename, 'w+') as destination_file:
            print(f"Writing to {filename}... ", end="")
            destination_file.write(data)
            overwritten_files += 1
            print("Done.")

        for _ in range(len(folders)):
            os.chdir('../..')

    if overwritten_files:
        print(f"\nOverwrote {overwritten_files} files.")

    if modules:
        print(f"Created the following modules:\n- {"\n- ".join(modules)}")


def _set_local_ip(ip: str) -> None:
    global LOCAL_IP
    LOCAL_IP = ip


def get_local_ip() -> str:
    return LOCAL_IP


def establish_wifi_connection(timeout_ms: int = 10_000) -> network.WLAN | None:
    import time
    import sys

    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    _set_mac_address(sta_if.config("mac"))
    dhcp_hostname = get_hostname()
    sta_if.config(dhcp_hostname=dhcp_hostname)

    data = load_json(CREDENTIALS) or dict()
    known_networks = data.get("known_networks", dict())

    try:
        with open('last_connected_wifi.cfg') as file:
            last_connected_ssid = file.read()
    except OSError:
        last_connected_ssid = None

    import select
    p = select.poll()
    p.register(sys.stdin)

    for ssid in sorted(known_networks.keys(), key=lambda ssid: (ssid != last_connected_ssid, ssid)):
        password = known_networks[ssid]
        print(f"Attempting to connect to {ssid}...")
        sta_if.connect(ssid, password)
        start_connection_time = time.ticks_ms()
        while not sta_if.isconnected() and (
        passed_time := time.ticks_diff(time.ticks_ms(), start_connection_time)) <= timeout_ms:
            _, flags = p.poll(0)[0]
            if flags & 1:
                cmd = sys.stdin.read(1)
                if cmd == "s":
                    break
            print_progress_bar(passed_time, timeout_ms, prefix='Connecting:', suffix='remaining ', length=48)
            pass
        if not sta_if.isconnected():
            print_progress_bar(passed_time, timeout_ms, prefix='Connecting:', suffix='TIMED OUT ', length=48,
                               print_end='\n')
            sta_if.disconnect()
        else:
            print_progress_bar(passed_time, timeout_ms, prefix='Connecting:', suffix='CONNECTED ', length=48,
                               print_end='\n')
            print(f"Successfully connected to {ssid} as {dhcp_hostname}.")
            with open("last_connected_wifi.cfg", "w+") as file:
                file.write(ssid)
            break

    if sta_if.isconnected():
        _set_local_ip(sta_if.ifconfig()[0])
        return sta_if
    else:
        print("Failed to establish a WiFi connection.")
        return None


def establish_lan_connection() -> network.LAN | None:
    import time
    print(f"Attempting to establish a LAN connection...")
    try:
        lan = network.LAN(mdc=machine.Pin(23),
                          mdio=machine.Pin(18),
                          phy_type=network.PHY_LAN8720,
                          phy_addr=1,
                          power=machine.Pin(16),
                          id=0)
    except OSError:
        print("Failed to establish LAN connection: No Ethernet port present")
        return None

    _set_mac_address(lan.config("mac"))
    lan.active(True)
    lan.config(dhcp_hostname=get_hostname())
    start_connection_time = time.ticks_ms()
    while not lan.isconnected() and time.ticks_diff(time.ticks_ms(), start_connection_time) <= 10000:
        pass
    if not lan.isconnected():
        print("Failed to establish LAN connection: Connection timed out. (not plugged in?)")
        return None
    _set_local_ip(lan.ifconfig()[0])
    print(f"Successfully connected to the LAN network as {get_hostname()} with IP {lan.ifconfig()[0]}")
    return lan


# Print iterations progress
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    seconds = "{:.1f}".format(abs((total - iteration) / 1000))
    filled_length = int(length * (1 - (iteration / total)))
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {seconds}s {suffix}', end=print_end)
    # Print New Line on Complete
    if iteration == total:
        print()


def rm(d):  # Remove file or tree
    import os
    try:
        if os.stat(d)[0] & 0x4000:  # Dir
            for f in os.ilistdir(d):
                if f[0] not in ('.', '..'):
                    rm("/".join((d, f[0])))  # File or Dir
            print(f"Removing directory {d}...")
            os.rmdir(d)
        else:  # File
            print(f"Removing file {d}...")
            os.remove(d)
    except:
        print("rm of '%s' failed" % d)


def rm_all(whitelist: list[str]|None = None):
    import os
    if whitelist is None:
        whitelist = []
    whitelist += [f"{__name__}.py", "boot.py", "credentials.py", "webrepl_cfg.py"]
    for d in os.listdir():
        if d in whitelist:
            continue
        rm(d)
    print(f"Removed all files and directories except:\n- {"\n- ".join(file for file in whitelist if file in os.listdir())}")


def load_json(filename: str) -> dict | None:
    import ujson
    # Load existing data
    try:
        with open(filename, "r") as file:
            return ujson.load(file)
    except OSError:
        return None


def dump_json(filename: str, data: dict) -> None:
    import ujson
    with open(filename, "w+") as file:
        ujson.dump(data, file)


def save_network(ssid: str, password: str) -> None:
    import ujson

    data = load_json(CREDENTIALS) or dict()

    if not data.get("known_networks"):
        data["known_networks"] = dict()

    # Add or update the SSID
    data["known_networks"][ssid] = password

    # Save it back
    with open(CREDENTIALS, "w") as file:
        ujson.dump(data, file)

    print(f"Added/Updated network: {ssid}")


def list_saved_networks() -> None:
    data = load_json(CREDENTIALS)
    print(data["known_networks"])

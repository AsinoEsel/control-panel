def get_mac_address() -> str:
    from binascii import hexlify
    import network
    sta_if = network.WLAN(network.STA_IF)
    mac_raw = sta_if.config('mac')
    return hexlify(mac_raw, ':').decode().upper()


def get_hostname() -> str:
    import ujson
    with open("hostname_manifest.json") as f:
        data = ujson.load(f)
    name = data.get(get_mac_address())
    del data
    return name or "ControlPanelESP"


def create_ap(ssid, password, authmode):
    import network
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid=ssid, password=password, authmode=authmode)
    print('Created an AP with SSID:', ssid)


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
            print(f"Writing to {filename}...")
            destination_file.write(data)
            overwritten_files += 1

        for _ in range(len(folders)):
            os.chdir('../..')

    if overwritten_files:
        print(f"\nOverwrote {overwritten_files} files.")

    if modules:
        print(f"Created the following modules:\n- {"\n- ".join(modules)}")


def establish_wifi_connection(timeout_ms: int = 10_000):
    from credentials import KNOWN_NETWORKS, AP_SSID, AP_PASSWORD
    import network
    import time
    import sys

    try:
        with open('last_connected_wifi.cfg') as file:
            last_connected_ssid = file.read()
    except OSError:
        last_connected_ssid = None

    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    dhcp_hostname = get_hostname()
    sta_if.config(dhcp_hostname=dhcp_hostname)

    import select
    p = select.poll()
    p.register(sys.stdin)

    for ssid in sorted(KNOWN_NETWORKS.keys(), key=lambda ssid: (ssid != last_connected_ssid, ssid)):
        password = KNOWN_NETWORKS[ssid]
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

    if not sta_if.isconnected():
        create_ap(AP_SSID, AP_PASSWORD, authmode=3)


def establish_lan_connection():
    import network
    import machine

    lan = network.LAN(mdc=machine.Pin(23), mdio=machine.Pin(18), phy_type=network.PHY_LAN8720, phy_addr=1,
                      power=machine.Pin(16), id=0)
    lan.active(True)
    lan.ifconfig()


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


def add_known_network(new_ssid: str, new_password: str):
    from credentials import KNOWN_NETWORKS, AP_SSID, AP_PASSWORD
    data = 'KNOWN_NETWORKS = {\n'
    for ssid, password in KNOWN_NETWORKS.items():
        data += f'    "{ssid}": "{password}",\n'
    data += f'    "{new_ssid}": "{new_password}",\n'
    data += '}\n'
    data += f'AP_SSID, AP_PASSWORD = "{AP_SSID}", "{AP_PASSWORD}"\n'

    with open("credentials.py", "w") as f:
        f.write(data)

from controlpanel.scripts import ControlAPI, Event
import time

rfid_scan_time: float = 0.0


@ControlAPI.callback("TestRFIDReader", "RFID", (98, 97, 100, 100, 97, 116, 97))
def rfid_scanned(event: Event):
    global rfid_scan_time
    rfid_scan_time = event.timestamp


def start_countdown():
    print("starting countdown")
    for i in range(10):
        print(10-i)
        display = ControlAPI.devices.get("Display1")
        display.text = str(10-i)
        time.sleep(1)


@ControlAPI.callback("TestButton", None, True, allow_parallelism=False)
def dostuff(event: Event):
    if time.time() - rfid_scan_time > 10.0:
        return
    start_countdown()

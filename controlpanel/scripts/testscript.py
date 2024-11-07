from controlpanel.scripts import ControlAPI, Event
import time

lever_flipped = False
flip_time: float = 0.0


@ControlAPI.callback("TestRFIDReader", "RFID", (98, 97, 100, 100, 97, 116, 97))
def flip_lever(event: Event):
    global lever_flipped, flip_time
    lever_flipped = True
    flip_time = event.timestamp


def start_countdown():
    print("starting countdown")
    for i in range(10):
        print(10-i)
        display = ControlAPI.devices.get("Display1")
        display.text = str(10-i)
        time.sleep(1)


@ControlAPI.callback("TestButton", None, True, allow_parallelism=True)
def print_dog(event: Event):
    if not lever_flipped or time.time() - flip_time > 10.0:
        return
    start_countdown()

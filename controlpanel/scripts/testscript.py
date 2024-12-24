from controlpanel.scripts import ControlAPI, Event
import time
from controlpanel.event_manager.dummy import *

rfid_scan_time: float = 0.0


@ControlAPI.callback("TestRFIDReader", "RFID", (98, 97, 100, 100, 97, 116, 97))
def rfid_scanned(event: Event):
    global rfid_scan_time
    rfid_scan_time = event.timestamp


@ControlAPI.callback("BigRedButton", None, None)
def turn_on_motor(event: Event):
    chronometer: DummyPWM = ControlAPI.devices.get("Chronometer")
    if event.value:
        chronometer.intensity = 1.0
    else:
        chronometer.intensity = 0.0
    # color_val = (255, 255, 255) if event.value else (0, 0, 0)
    # leds: DummyLEDStrip = ControlAPI.devices.get("ChronometerLampen")
    # leds[0] = color_val


def start_countdown():
    for i in range(10):
        print(10-i)
        display = ControlAPI.devices.get("Display1")
        display.text = str(10-i)
        time.sleep(1)


entered_numbers: list[int] = []


@ControlAPI.callback("RotaryDial", None, None, allow_parallelism=False)
def rotary_callback(event: Event):
    number = event.value
    entered_numbers.append(number)
    seven_segment: DummySevenSegmentDisplay = ControlAPI.devices.get("SevenSegmentDisplay")
    seven_segment.set_text("".join(str(number) for number in entered_numbers))
    if len(entered_numbers) >= 8:
        for i in range(8):
            time.sleep(0.5)
            first_half = "".join(str(number) for number in entered_numbers[:i])
            second_half = "".join(str(number) for number in entered_numbers[i+1:]) if i < 8 else ""
            seven_segment.set_text(first_half + " " + second_half)
        time.sleep(0.5)
        seven_segment.set_text("AAAAAAAAAAAAAAAA")
        time.sleep(3)
        entered_numbers.clear()
        seven_segment.set_text(" ")


@ControlAPI.callback("DialReset")
def rotary_reset_callback(event: Event):
    entered_numbers.clear()
    seven_segment: DummySevenSegmentDisplay = ControlAPI.devices.get("SevenSegmentDisplay")
    seven_segment.set_text(" ")


@ControlAPI.callback("TestButton", None, True, allow_parallelism=False)
def dostuff(event: Event):
    if time.time() - rfid_scan_time > 10.0:
        return
    start_countdown()

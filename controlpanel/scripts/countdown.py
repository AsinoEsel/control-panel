import time
import datetime
from controlpanel.scripts import ControlAPI, Event

from fourteensegment import Display, rgb_to_b16

UNIVERSE = 14
DISPLAY_COUNT = 3


@ControlAPI.callback(event_name="StartCountdown")
def start_countdown(event: Event):
    # target = datetime.now() + timedelta(seconds=event.value)

    today = datetime.datetime.now()
    target = datetime.datetime.combine(today.date(), datetime.time(18, 0))

    display = Display(DISPLAY_COUNT)
    display.clear()

    run = True
    while run:
        now = datetime.datetime.now()
        diff = (target - now)
        # print(diff)
        if diff > datetime.timedelta(minutes=60):
            string = " 0" + str(diff)[0:4] + "h" if diff.seconds % 2 == 0 else " 0" + str(diff)[0:4].replace(":", "") + " "
            color = rgb_to_b16(0, 255, 0)
        elif diff > datetime.timedelta(seconds=60):
            string = " " + str(diff)[2:7] + " " if diff.seconds % 2 == 0 else " " + str(diff)[2:7].replace(":", "") + " "
            color = rgb_to_b16(0, 255, 0)
        elif diff > datetime.timedelta(seconds=15):
            string = " " + str(diff)[5:10].replace(".", ":") + " "
            color = rgb_to_b16(255, 0, 0)
        elif diff > datetime.timedelta(seconds=0):
            string = " " + str(diff)[5:10].replace(".", ":") + " "
            color = rgb_to_b16(255, 0, 0) if (diff * 2).seconds % 2 == 0 else rgb_to_b16(128, 0, 0)
        else:
            string = " 00:00 "
            color = rgb_to_b16(255, 0, 0)
            ControlAPI.fire_event("countdown.py", "TimeRanOut")
            run = False
        # print(string)
        display.send_dmx(UNIVERSE, 0, display.text_to_data(string, color))
        time.sleep(0.055)


if __name__ == "__main__":
    start_countdown()

from controlpanel.scripts import ControlAPI, Event


battery_is_plugged_in = False
battery_power = 100


@ControlAPI.call_with_frequency(0.1)
def drain_battery():
    global battery_power
    battery_power -= 1


@ControlAPI.callback("BatteryButtonLadestation", "PushButton", None)
@ControlAPI.callback("BatteryButton", "PushButton", None)
def callback_battery(event: Event):
    global battery_is_plugged_in

    if event.value is False:
        battery_is_plugged_in = False
        return

    if "ladestation" in event.name.lower():
        battery_is_plugged_in = "ladestation"
    else:
        battery_is_plugged_in = "bvgpanel"

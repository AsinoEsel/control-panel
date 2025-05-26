from controlpanel.scripts import ControlAPI, Event
from controlpanel.event_manager.dummy import DummyLEDStrip

MODS_PER_ROW = 5
MODS_PER_COLUMN = 3
TOTAL_KEYS = MODS_PER_COLUMN * MODS_PER_ROW * 16


def col(a):
    a %= 16 * MODS_PER_ROW
    return 3 - (a % 4) + ((a // 16) * 4)


def row(a):
    tmp = 3 - (a % 16) // 4
    return tmp + (a // (16 * MODS_PER_ROW)) * 4



# for i in range(16 * MODS_PER_ROW * MODS_PER_COLUMN):
#     print(i, f"row: {row(i)}, col: {col(i)}")


# old_states: list[int] = [0 for _ in range(TOTAL_KEYS)]
# old_states: bytes = b""

@ControlAPI.callback("MainframeKeys", "ButtonsChanged", None)
def keyboard_callback(event: Event):
    keyboard_leds: DummyLEDStrip = ControlAPI.get_device("MainframeLEDs")

    global old_states
    # states = [byte for byte in event.value]




    # new_states: list[int] = [b << 7 for b in event.value]
    # state_diff = [old_states[i] ^ new_states[i] for i in range(len(old_states))]

    # changes = [i for i, e in enumerate(state_diff) if e != 0]

    # print(changes)

    print(event.value)

    dmx_data = bytearray(1 + TOTAL_KEYS)
    # for button_id in changes:
    for (button_id, button_state) in event.value:
        led_coord = 15 - (button_id % 16) + (button_id // 16) * 16
        if button_state is True:
            dmx_data[1 + led_coord] = keyboard_leds.compress_rgb((0, 128, 0))
        else:
            dmx_data[1 + led_coord] = keyboard_leds.compress_rgb((0, 0, 0))

    keyboard_leds.send_dmx_data(dmx_data)

    # old_states = new_states


    # new_states = list[int] = [0 for _ in range(MODS_PER_COLUMN * MODS_PER_COLUMN * 16)]
    # new_states = [0 for i in range(len(states)) if states[i] == old_states[i]]
    #
    # print(states)

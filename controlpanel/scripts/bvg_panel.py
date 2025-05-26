from controlpanel.scripts import ControlAPI, Event


def callback_bvgpanel_button(event: Event):
    button_id = int(event.source[12:])
    print("PRESSED BUTTON!", button_id, event.value)
    star_bars = (ControlAPI.dmx.devices.get("StarBar1"), ControlAPI.dmx.devices.get("StarBar2"))
    for star_bar in star_bars:
        if star_bar is not None:
            star_bar.function = button_id

    toggle_buttons = [hash(str(button_id+36*i)) % 36 for i in range(5)]
    bvg_panel = ControlAPI.get_device("TestBVGPanel")

    for button in toggle_buttons:
        bvg_panel._output_states[button] = not bvg_panel._output_states[button]
    bvg_panel.send_dmx_data()


@ControlAPI.callback("TestBVGPanel", "Digit", None)
def callback_bvgpanel_address(event: Event):
    print("Address is ", event.value)


for i in range(47):
    ControlAPI.subscribe(callback_bvgpanel_button, f"TestBVGPanel{i}", "PushButton", True)

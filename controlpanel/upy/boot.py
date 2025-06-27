import webrepl
import utils

utils.create_modules()

# Attempt to establish a network connection: LAN > WLAN (STA) > WLAN (AP)
lan = utils.establish_lan_connection()
if not lan:
    sta_if = utils.establish_wifi_connection()
    if not sta_if:
        ap_if = utils.create_ap()

webrepl.start()
print(f"MAC address is {utils.get_mac_address()}")

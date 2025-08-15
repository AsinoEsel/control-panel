import webrepl
import utils

utils.create_modules()

# Attempt to establish a network connection: LAN > WLAN (STA) > WLAN (AP)
interface = utils.establish_connection()

webrepl.start()
print(f"MAC address is {utils.get_mac_address()}")

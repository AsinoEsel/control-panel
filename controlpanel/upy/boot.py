import webrepl
import utils

utils.create_modules()
utils.establish_wifi_connection()
webrepl.start()
print(f"MAC address is {utils.get_mac_address()}")

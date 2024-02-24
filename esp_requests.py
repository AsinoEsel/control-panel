import requests
from account_manager import User


class ESP:
    def __init__(self, IP: str, level_name: str) -> None:
        self.IP = IP
        self.level_name = level_name
        self.checked_in_users: list[User] = []
    
    async def call(self, operation, val=None) -> requests.Response|str:
        url = "http://" + self.IP + "/api"
        params = {"operation": operation}
        if val is not None:
            params["value"] = val
        try:
            response = requests.get(url, params=params, timeout=10)
            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as error:
            return error


ESP_seven_segment = ESP("192.168.1.36", "Cockpit")
# ESP_seven_segment = ESP("192.168.0.150", "Cockpit")
ESPs = {
    ESP_seven_segment.IP: ESP_seven_segment,
}


def debug_send_request(esp, max_tries=10, interval=1):
    from time import sleep
    operation = "display"
    val = 0
    while val <= max_tries:
        control_panel.schedule_async_task(esp, operation, str(val))
        print(f"Request sent to {esp.IP} with operation '{operation}' and value '{str(val)}'")
        val += 1
        sleep(interval)
    print("Finished debug.")

if __name__ == "__main__":
    # Test an esp
    from control_panel import ControlPanel
    from time import sleep
    control_panel = ControlPanel()
    
    debug_send_request(ESP_seven_segment)
    while not all([future.done() for future in control_panel.futures]):
        print("Waiting for all responses to come in...")
        sleep(1)
    for future in control_panel.futures:
        print(future.result())
    
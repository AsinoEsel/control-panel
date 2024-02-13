import requests
import asyncio

# Function to start and run the asyncio event loop
def start_asyncio_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()
    
class ESP:
    def __init__(self, IP: str) -> None:
        self.IP = IP
    
    async def call(self, operation, val=None) -> requests.Response:
        url = "http://" + self.IP + "/api"
        params = {"operation": operation}
        if val is not None:
            params["value"] = val
        response = requests.get(url, params=params)
        return response
    

ESP_seven_segment = ESP("192.168.1.36")


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
    
    from main import ControlPanel
    from time import sleep
    control_panel = ControlPanel()
    
    debug_send_request(ESP_seven_segment)
    while not all([future.done() for future in control_panel.futures]):
        print("Waiting for all responses to come in...")
        sleep(1)
    for future in control_panel.futures:
        print(future.result())
    
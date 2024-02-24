import pygame as pg
from window_manager import WindowManager
from account_manager import AccountManager
import asyncio
from esp_requests import ESP
import threading


class ControlPanel:
    def __init__(self, run_window_manager: bool = True, fullscreen: bool = False) -> None:
        self.button_is_pressed = False
        self.button_press_acknowledged = False
        
        if run_window_manager:        
            self.window_manager = WindowManager(self, fullscreen)
        self.account_manager = AccountManager()
        
        self.loop = asyncio.new_event_loop()
        
        loop_thread = threading.Thread(target=self.start_asyncio_loop, daemon=True)
        loop_thread.start()
        self.futures: list[asyncio.Future] = []
    
    def start_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def schedule_async_task(self, esp: ESP, operation, val=None):
        if not self.loop.is_running():
            print("Loop is not running")
            return
        self.futures.append(asyncio.run_coroutine_threadsafe(esp.call(operation, val), self.loop))
    
    def press_button():
        pass
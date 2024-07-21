import pygame as pg
from window_manager import WindowManager
from account_manager import AccountManager
import asyncio
from esp_requests import ESP
import threading


class ControlPanel:
    def __init__(self, *, fullscreen: bool = False, use_shaders: bool = True, maintain_aspect_ratio: bool = True) -> None:
        self.button_is_pressed = False
        self.button_press_acknowledged = False
        
        self.account_manager = AccountManager()
        
        self.loop = asyncio.new_event_loop()
        
        loop_thread = threading.Thread(target=self.start_asyncio_loop, daemon=True)
        loop_thread.start()
        self.futures: list[asyncio.Future] = []
                
        self.window_manager = WindowManager(self, fullscreen=fullscreen, use_shaders=use_shaders, maintain_aspect_ratio=maintain_aspect_ratio)
                    
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
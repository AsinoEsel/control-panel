import pygame as pg
from window_manager import WindowManager
from account_manager import AccountManager
import asyncio


class ControlPanel:
    def __init__(self, *, fullscreen: bool = False, use_shaders: bool = True, maintain_aspect_ratio: bool = True) -> None:        
        self.account_manager = AccountManager()
        self.loop = asyncio.new_event_loop()                
        self.window_manager = WindowManager(self, fullscreen=fullscreen, use_shaders=use_shaders, maintain_aspect_ratio=maintain_aspect_ratio)
        
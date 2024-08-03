from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT, CHAR_HEIGHT, DEFAULT_FONT, DEFAULT_GAP
import pygame as pg
from .widget import Window, TextField
from .input_box import InputBox, InputBoxPassword


class LoginWindow(Window):
    def __init__(self, parent) -> None:
        super().__init__(parent, "Login", RENDER_WIDTH//4, RENDER_HEIGHT//4, "Please enter your login credentials.", RENDER_WIDTH//2-RENDER_WIDTH//8, RENDER_HEIGHT//2-RENDER_HEIGHT//8, DEFAULT_FONT)
        username_text = TextField(self, self.rect.w//8, self.rect.h//2, 3*self.rect.w//8, CHAR_HEIGHT[DEFAULT_FONT]*1.3, "Login:", True)
        password_text = TextField(self, 3*DEFAULT_GAP, 3*self.rect.h//4, 3*self.rect.w//8, CHAR_HEIGHT[DEFAULT_FONT]*1.3, "Password:", True)
        self.username_input = InputBox(self, 3*self.rect.w//8, self.rect.h//2, self.rect.w//2)
        self.password_input = InputBoxPassword(self, 3*self.rect.w//8, 3*self.rect.h//4, self.rect.w//2)
        self.add_element(username_text)
        self.add_element(self.username_input)
        self.add_element(password_text)
        self.add_element(self.password_input)
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.close()
                if value := self.get_root().control_panel.account_manager.attempt_login(username=self.username_input.text, password=self.password_input.text):
                    self.get_root().terminal.log.print_to_log(f"Logged in as {value.username}", (255,255,0))
                else:
                    self.get_root().terminal.log.print_to_log(f"Could not log in as {self.username_input.text}", (255,0,0))
                return
            if event.key == pg.K_ESCAPE:
                return
        super().handle_event(event)

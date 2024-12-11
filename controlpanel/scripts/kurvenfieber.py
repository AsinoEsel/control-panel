from kurvenfieber import Kurvenfieber
from controlpanel.scripts import ControlAPI

ControlAPI.add_game(Kurvenfieber(tickrate=30, timescale=1.0), make_current=True)

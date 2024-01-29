import pygame as pg
pg.init()

BACKGROUND_COLOR = pg.Color((16,16,16))
COLOR_INACTIVE = pg.Color((0, 128, 0))
COLOR_ACTIVE = pg.Color((0,255,0))
FONT_SIZE = 32
FONT = pg.font.Font("C:/Windows/Fonts/cour.ttf", FONT_SIZE)
CHAR_WIDTH = FONT.render("|", False, (0, 0, 0)).get_width()
CHAR_HEIGHT = FONT.render("|", False, (0, 0, 0)).get_height()
print(CHAR_HEIGHT)

DEFAULT_GAP = 6
LINE_THICKNESS_THIN = 2
LINE_THICKNESS_THICK = 4
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
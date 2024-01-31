import pygame as pg
import os
pg.init()

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BACKGROUND_COLOR = pg.Color((16,16,16))
COLOR_INACTIVE = pg.Color((0, 128, 0))
COLOR_ACTIVE = pg.Color((0,255,0))
ACCENT_COLOR_INACTIVE = pg.Color((0,32,0))
ACCENT_COLOR_ACTIVE = pg.Color((0, 64, 0))
DEBUG_COLOR = pg.Color((255,20,147))
DEBUG_LONG_TEXT = """What the dog doin'? But no, actually. What the fuck is the dog doing.\
Like, are you seeing this? Dude. Dude, check this out, it's almost as if it's...\
Oh my god. Oh god. It's coming. Run. RUN! FOR GOD'S SAKE RUN."""
DEFAULT_FONT = pg.font.Font(os.path.join("media","clacon2.ttf"), 32)
SMALL_FONT = pg.font.Font(os.path.join("media","clacon2.ttf"), 12)

CHAR_WIDTH = {
    DEFAULT_FONT: DEFAULT_FONT.render("|", False, (0, 0, 0)).get_width()
}

CHAR_HEIGHT = {
    DEFAULT_FONT: DEFAULT_FONT.render("Ög", False, (0, 0, 0)).get_height()
}

DEFAULT_GAP = 6
LINE_THICKNESS_THIN = 2
LINE_THICKNESS_THICK = 4

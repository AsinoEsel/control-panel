import pygame as pg
pg.mouse.set_visible(False)

cursor_surface = pg.image.load("media/cursor.png")
mult_surface = pg.Surface(cursor_surface.get_size())
mult_surface.fill((0,255,0))
cursor_surface.blit(mult_surface, (0,0), special_flags=pg.BLEND_MULT)
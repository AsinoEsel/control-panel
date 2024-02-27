import random
import math
import pygame

class GameObject:
    def __init__(self, pos, last_hit=0, visible=False):
        self.pos = pos
        self.last_hit = last_hit
        self.visible = visible

    @classmethod
    def create(cls, center, radius):
        angle = random.uniform(0, 2 * math.pi)
        rand_radius = random.random() * radius
        x = center[0] + rand_radius * math.cos(angle)
        y = center[1] + rand_radius * math.sin(angle)
        pos = (x, y)
        return cls(pos)

    @classmethod
    def create_from_png(cls, image_path):
        img = pygame.image.load(image_path)
        img_size = img.get_size()
        
        if img_size != (800, 600):
            print("Warning: Image is not 800x600!")
        
        objects = []
        for x in range(img_size[0]):
            for y in range(img_size[1]):
                r, g, b, _ = img.get_at((x, y))
                if (r, g, b) == (255, 0, 0):
                    objects.append(cls((x, y)))
        return objects

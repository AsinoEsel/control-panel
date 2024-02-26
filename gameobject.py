import random
import math
from PIL import Image

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
        objects = []
        with Image.open(image_path) as img:
            if img.size != (800, 600):
                print("Warning: Image is not 800x600!")
            for x in range(img.width):
                for y in range(img.height):
                    r, g, b, _ = img.getpixel((x, y))
                    if (r, g, b) == (255, 0, 0):
                        objects.append(cls((x, y)))
        return objects

# image_path = 'red_dot_image.png'
# objects = GameObject.create_from_png(image_path)
# for obj in objects:
#     print(f'Pos: {obj.pos}')

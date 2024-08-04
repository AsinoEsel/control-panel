import pygame as pg
import sys
import math
import pygame.gfxdraw
from .widget import Widget, Desktop
from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT


pygame.mixer.init()
sound = pygame.mixer.Sound("media/ping.wav")

class Dot:
    def __init__(self, pos, last_hit=0, visible=False):
        self.pos = pos
        self.last_hit = last_hit
        self.visible = visible
        self.visble_duration = 1

    @classmethod
    def create_random(cls, center, radius):
        import random
        angle = random.uniform(0, 2 * math.pi)
        rand_radius = random.random() * radius
        x = center[0] + rand_radius * math.cos(angle)
        y = center[1] + rand_radius * math.sin(angle)
        pos = (x, y)
        return cls(pos)

    @classmethod
    def create_from_png(cls, image_path):
        img = pg.image.load(image_path)
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


class Radar(Widget):
    BLACK = (5, 10, 5)
    GREEN = (50, 255, 25)
    DARK_GREEN = (0, 100, 0)
    TRANSPARENT = (0, 0, 0, 0)
    RED = (255, 0, 0)
    
    def __init__(self, parent: Desktop, png: str, x=0, y=0, w=RENDER_WIDTH, h=RENDER_HEIGHT) -> None: #self, width: int, height: int, png: str) -> None:
        super().__init__(parent, x, y, w, h)
        self.center = (w // 2, h // 2)
        self.radius = int(h/2 * 0.9)
        self.angle = 0
        self.angle_speed = 100
        self.sweep_width = 1
        self.dots = Dot.create_from_png(png)
        self.angular_cross_sections = 12
        self.radial_cross_sections = 8

    def is_within_radar(self, pos):
        return (pos[0] - self.center[0]) ** 2 + (pos[1] - self.center[1]) ** 2 <= self.radius**2

    def is_in_sweep_sector(self, dot_pos, dt):
        # Check distance
        distance_to_dot_squared = (dot_pos[0] - self.center[0])**2 + (dot_pos[1] - self.center[1])**2
        if distance_to_dot_squared > self.radius**2:
            return False

        # Check angle
        dot_angle = math.degrees(math.atan2(dot_pos[1] - self.center[1], dot_pos[0] - self.center[0])) % 360

        # Adjust sweep angle to be within 0-360
        last_angle = self.angle - dt * self.angle_speed / 1000

        sweep_start_angle = (last_angle - self.sweep_width  / 2) % 360
        sweep_end_angle   = (self.angle + self.sweep_width / 2) % 360

        self._tmp_angle = self.angle

        """print("start: " , sweep_start_angle)
        print("end  : " , sweep_end_angle)
        print("last : " , last_angle)
        print("dt: " , dt)"""

        # Check if object is within the sweep sector
        if sweep_start_angle < sweep_end_angle:
            return sweep_start_angle <= dot_angle <= sweep_end_angle
        else:
            return obj_angle >= sweep_start_angle or obj_angle <= sweep_end_angle
    
    def render(self):
        self.surface.fill(self.BLACK)

        # Draw radar circle
        pg.gfxdraw.aacircle(self.surface, self.center[0], self.center[1], self.radius, self.D_GREEN)

        radius_qarter = self.radius/4
        pg.gfxdraw.aacircle(self.surface, self.center[0], self.center[1], int(self.radius - 1 * radius_qarter), self.D_GREEN)
        pg.gfxdraw.aacircle(self.surface, self.center[0], self.center[1], int(self.radius - 2 * radius_qarter), self.D_GREEN)
        pg.gfxdraw.aacircle(self.surface, self.center[0], self.center[1], int(self.radius - 3 * radius_qarter), self.D_GREEN)
        pg.gfxdraw.aacircle(self.surface, self.center[0], self.center[1], int(self.radius - 0.2 * radius_qarter), self.D_GREEN)

        # cross
        pg.draw.line(self.surface, self.D_GREEN, (self.center[0]-self.radius, self.center[1]), (self.center[0]+self.radius, self.center[1]), 1)
        pg.draw.line(self.surface, self.D_GREEN, (self.center[0], self.center[1] + self.radius), (self.center[0], self.center[1] - self.radius), 1)

        current_time = pg.time.get_ticks()

        # Draw and update objects
        for obj in self.objects:
            if self.is_in_sweep_sector(obj.pos):
                obj.visible = True
                obj.last_hit = current_time
            if obj.visible and current_time - obj.last_hit <= 1000:
                pg.draw.circle(self.surface, self.RED, obj.pos, 5)
            elif current_time - obj.last_hit > 1000:
                obj.visible = False

        # Draw radar sweep (optional: visualize the sweep sector)
        end_x_front = self.center[0] + math.cos(math.radians(self.angle - self.sweep_width/2)) * self.radius
        end_y_front = self.center[1] + math.sin(math.radians(self.angle - self.sweep_width/2)) * self.radius
        end_x_end   = self.center[0] + math.cos(math.radians(self.angle + self.sweep_width/2)) * self.radius
        end_y_end   = self.center[1] + math.sin(math.radians(self.angle + self.sweep_width/2)) * self.radius
        
        pg.draw.polygon(self.surface, self.GREEN, (self.center,(end_x_front, end_y_front), (end_x_end, end_y_end)))    
    
    def update(self, tick: int, dt: int, joysticks: dict[int: pg.joystick.JoystickType]):
        # Increment angle for sweep movement
        self.angle += dt*self.angle_speed/1000
        if self.angle >= 360:
            self.angle = self.angle % 360
        self.flag_as_needing_rerender()
    


        #print("==ANGLE==", self.angle)

if __name__ == '__main__':
    from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT
    pg.init()
    clock = pg.time.Clock()
    width, height = RENDER_WIDTH, RENDER_HEIGHT

    screen = pg.display.set_mode((RENDER_WIDTH, RENDER_HEIGHT))
    
    radar = Radar(RENDER_WIDTH, RENDER_HEIGHT, png='media/red_dot_image.png')

    running = True
    dt = 0
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
        radar.render_cross_section(screen)

        sweep_surface.fill(radar.TRANSPARENT)
        radar.render_sweep(sweep_surface, dt)

        screen.blit(sweep_surface, (0, 0))

        pg.display.flip()
        dt = clock.tick(30)

    pg.quit()
    sys.exit()

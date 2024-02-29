import pygame
import sys
import math
import pygame.gfxdraw

pygame.mixer.init()
sound = pygame.mixer.Sound("media/ping.wav")

class Dot:
    def __init__(self, pos, last_hit=0, visible=False):
        self.pos = pos
        self.last_hit = last_hit
        self.visible = visible

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


class Radar:
    BLACK = (5, 10, 5)
    GREEN = (50, 255, 25)
    DARK_GREEN = (0, 100, 0)
    TRANSPARENT = (0, 0, 0, 0)
    RED = (255, 0, 0)
    
    def __init__(self, width: int, height: int, png: str) -> None:
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.radius = int(height/2 * 0.9)
        self.angle = 0
        self.angle_speed = 100
        self.sweep_width = 1
        self.dots = Dot.create_from_png(png)
        self.angular_cross_sections = 12
        self.radial_cross_sections = 8

        self._tmp_angle = 0

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

        print("start: " , sweep_start_angle)
        print("end  : " , sweep_end_angle)
        print("last : " , last_angle)
        print("dt: " , dt)

        # Check if object is within the sweep sector
        if sweep_start_angle < sweep_end_angle:
            return sweep_start_angle <= dot_angle <= sweep_end_angle
        else:
            return dot_angle >= sweep_start_angle or dot_angle <= sweep_end_angle
        
    def render_cross_section(self, surface: pygame.Surface):
        surface.fill(self.BLACK)

        for i in range(0, self.radial_cross_sections + 1):
            i = i / (self.radial_cross_sections)
            pygame.gfxdraw.aacircle(surface, self.center[0], self.center[1], int(self.radius * i), self.DARK_GREEN)
        pygame.gfxdraw.aacircle(surface, self.center[0], self.center[1], int(self.radius * 0.98), self.DARK_GREEN)

        angle_between_lines = 360 / self.angular_cross_sections # Calculate angle between cross_section lines
    
        for i in range(self.angular_cross_sections// 2):
            angle = math.radians(angle_between_lines * i)

            start_x = self.center[0] + math.cos(angle) * self.radius
            start_y = self.center[1] + math.sin(angle) * self.radius
            end_x =   self.center[0] - math.cos(angle) * self.radius
            end_y =   self.center[1] - math.sin(angle) * self.radius

            pygame.draw.line(surface, self.DARK_GREEN, (start_x, start_y), (end_x, end_y), 1)
    
    def render_sweep(self, surface: pygame.Surface, dt: int):
        current_time = pygame.time.get_ticks()

        # Draw and update objects
        for dot in self.dots:
            if self.is_in_sweep_sector(dot.pos, dt):
                dot.visible = True
                sound.play()
                dot.last_hit = current_time
            if dot.visible and current_time - dot.last_hit <= self.angle_speed / dt:
                pygame.draw.circle(surface, self.RED, dot.pos, 5) # TODO add tickrate * 5
            else:
                dot.visible = False

        end_x_front = self.center[0] + math.cos(math.radians(self.angle - self.sweep_width/2)) * self.radius
        end_y_front = self.center[1] + math.sin(math.radians(self.angle - self.sweep_width/2)) * self.radius
        end_x_end   = self.center[0] + math.cos(math.radians(self.angle + self.sweep_width/2)) * self.radius
        end_y_end   = self.center[1] + math.sin(math.radians(self.angle + self.sweep_width/2)) * self.radius
        
        pygame.draw.polygon(surface, self.GREEN, (self.center,(end_x_front, end_y_front), (end_x_end, end_y_end)))

        self.angle += dt * self.angle_speed / 1000
        if self.angle >= 360:
            self.angle = self.angle % 360

        print("==ANGLE==", self.angle)

if __name__ == '__main__':
    from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT
    pygame.init()
    clock = pygame.time.Clock()
    width, height = RENDER_WIDTH, RENDER_HEIGHT

    screen = pygame.display.set_mode((RENDER_WIDTH, RENDER_HEIGHT))
    sweep_surface = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT), pygame.SRCALPHA)

    radar = Radar(RENDER_WIDTH, RENDER_HEIGHT, png='media/red_dot_image.png')

    running = True
    dt = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        radar.render_cross_section(screen)

        sweep_surface.fill(radar.TRANSPARENT)
        radar.render_sweep(sweep_surface, dt)

        screen.blit(sweep_surface, (0, 0))

        pygame.display.flip()
        dt = clock.tick(30)

    pygame.quit()
    sys.exit()

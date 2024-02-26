import pygame
import sys
import math
import numpy as np
from scipy.ndimage.filters import gaussian_filter
from gameobject import GameObject

# screen settings
width, height = 800, 600
clock = pygame.time.Clock()

# colors
black = (5, 10, 5)
green = (0, 255, 0)
red = (255, 0, 0)

# radar settings
center = (width // 2, height // 2)
radius = 280
angle = 0
sweep_width = 6
angle_speed = 2

# crt effects
scanline_distance = 600
scanline_timer = 600
scanline_speed = 3

# Generate random objects
num_objects = 10
# objects = [GameObject.create(center, radius) for _ in range(num_objects)]
objects = GameObject.create_from_png('media/red_dot_image.png')

def crt_scanlines(surface, crt_timer):
    for y in range(0, surface.get_height(), scanline_distance):
        pygame.draw.line(surface, (0, 50, 0, 100), (0, y + crt_timer), (surface.get_width(), y + crt_timer), 3)

def is_within_radar(pos, center, radius):
    """Check if a position is within the radar circle."""
    return math.sqrt((pos[0] - center[0]) ** 2 + (pos[1] - center[1]) ** 2) <= radius

def is_in_sweep_sector(obj_pos, sweep_angle, center, radius, sweep_width):
    """Check if an object is within the sweep sector."""
    # Check distance
    distance_to_obj = math.sqrt((obj_pos[0] - center[0])**2 + (obj_pos[1] - center[1])**2)
    if distance_to_obj > radius:
        return False

    # Check angle
    obj_angle = math.degrees(math.atan2(obj_pos[1] - center[1], obj_pos[0] - center[0])) % 360
    # Calculate distance to the object

    # Adjust sweep angle to be within 0-360
    sweep_start_angle = (sweep_angle - sweep_width // 2) % 360
    sweep_end_angle = (sweep_angle + sweep_width // 2) % 360

    # Check if object is within the sweep sector
    if sweep_start_angle < sweep_end_angle:
        return sweep_start_angle <= obj_angle <= sweep_end_angle
    else:
        return obj_angle >= sweep_start_angle or obj_angle <= sweep_end_angle

def renderer(surface):
    surface.fill(black)

    # Draw radar circle
    pygame.draw.circle(surface, green, center, radius, 3)

    radius_qarter = radius/4
    pygame.draw.circle(surface, green, center, radius - 1 * radius_qarter, 1)
    pygame.draw.circle(surface, green, center, radius - 2 * radius_qarter, 1)
    pygame.draw.circle(surface, green, center, radius - 3 * radius_qarter, 1)
    pygame.draw.circle(surface, green, center, radius - 0.2 * radius_qarter, 1)

    # cross
    pygame.draw.line(surface, green, (center[0]-radius, center[1]), (center[0]+radius, center[1]), 1)
    pygame.draw.line(surface, green, (center[0], center[1] + radius), (center[0], center[1] - radius), 1)

    # for scale in range(10):
    #     pygame.draw.line(screen, red, center[0] - )
    #     pass

    current_time = pygame.time.get_ticks()

    # Draw and update objects
    for obj in objects:
        if is_in_sweep_sector(obj.pos, angle, center, radius, sweep_width):
            obj.visible = True
            obj.last_hit = current_time
        if obj.visible and current_time - obj.last_hit <= 1000:
            pygame.draw.circle(surface, red, obj.pos, 5)
        elif current_time - obj.last_hit > 1000:
            obj.visible = False

    # Draw radar sweep (optional: visualize the sweep sector)
    # for sweep_angle in range(angle - sweep_width // 2, angle + sweep_width // 2):
    end_x_front = center[0] + math.cos(math.radians(angle - sweep_width/2)) * radius
    end_y_front = center[1] + math.sin(math.radians(angle - sweep_width/2)) * radius
    end_x_end   = center[0] + math.cos(math.radians(angle + sweep_width/2)) * radius
    end_y_end   = center[1] + math.sin(math.radians(angle + sweep_width/2)) * radius
    pygame.draw.polygon(surface, green, (center,(end_x_front, end_y_front), (end_x_end, end_y_end)))

    # crt timer
    scanline_timer += scanline_speed
    if scanline_timer >= scanline_distance:
        scanline_timer = 1
    crt_scanlines(surface, scanline_timer)


    screen_array = pygame.surfarray.array3d(surface)
    # screen_array = gaussian_filter(screen_array + (prev_array * 0.98) / 2, sigma=3).astype(int)
    
    pygame.surfarray.array_to_surface(surface, screen_array)

    prev_array = screen_array
    pygame.display.flip()

    # Increment angle for sweep movement
    angle += angle_speed
    if angle >= 360:
        angle = angle % 360


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((width, height))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        renderer(screen)

        # Cap the frame rate
        clock.tick(30)

    pygame.quit()
    sys.exit()

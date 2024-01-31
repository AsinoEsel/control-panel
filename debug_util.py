from pygame_monitor import Widget
import pygame as pg
import cv2
import numpy as np


def find_all_children(root: Widget) -> list[Widget]:
        visited = set()  # Set to keep track of visited nodes
        unique_children = []  # List to store unique children

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for child in node.elements:
                unique_children.append(child)
                dfs(child)

        dfs(root)
        return unique_children

def get_children_needs_updating(root) -> list[Widget]:
    needs_updating = []
    children = find_all_children(root)
    for child in children:
        if child.needs_updating:
            needs_updating.append(child)
    return needs_updating

def display_surface(surface: pg.Surface):
    surface_string = pg.image.tostring(surface, 'RGB')
    surface_np = np.frombuffer(surface_string, dtype=np.uint8).reshape((surface.get_height(), surface.get_width(), 3))
    surface_np = cv2.cvtColor(surface_np, cv2.COLOR_RGB2BGR)
    cv2.imshow('Surface', surface_np)
    cv2.waitKey(0)  # Wait indefinitely for a key press
    cv2.destroyAllWindows()
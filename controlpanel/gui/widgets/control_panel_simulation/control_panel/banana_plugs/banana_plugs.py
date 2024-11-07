from ....widget import Widget
import pygame as pg
from artnet import ArtNet


class Plug:
    def __init__(self, position: tuple[int, int], color: tuple[int, int, int], connection: int | None):
        self.position = position
        self.color = color
        self.connection = connection


class Socket:
    def __init__(self, position: tuple[int, int], color: tuple[int, int, int]):
        self.position = position
        self.color = color


class VirtualBananaPlugs(Widget):
    WIDTH = 100
    HEIGHT = 200
    PLUG_RADIUS = 8

    def __init__(self, artnet: ArtNet, parent: Widget, position: tuple[int, int], plug_count: int, socket_count: int, name: str):
        super().__init__(name, parent, position[0], position[1], self.WIDTH, self.HEIGHT, None)
        plug_distance = self.HEIGHT // plug_count
        self.plugs = [Plug((0, plug_distance//2 + i * plug_distance), (255, 0, 0), 1) for i in range(plug_count)]
        socket_distance = self.HEIGHT // socket_count
        self.sockets = [Socket((self.WIDTH, socket_distance//2 + i * socket_distance), (255, 255, 0)) for i in range(socket_count)]
        self.connections = [None for _ in range(plug_count)]

    def point_on_plug(self, plug: Plug, point: tuple[int, int], epsilon: float = 4.0):
        if pg.Vector2(point).distance_squared_to(pg.Vector2(plug.position)) < self.PLUG_RADIUS**2:
            return True

        if plug.connection is None:
            return False

        px, py = point
        ax, ay = plug.position
        bx, by = self.sockets[plug.connection].position

        # Calculate the differences
        dx = bx - ax
        dy = by - ay

        # Avoid division by zero if the line segment is vertical
        if abs(dx) < epsilon and abs(px - ax) < epsilon:
            return min(ay, by) - epsilon <= py <= max(ay, by) + epsilon

        if abs(dy) < epsilon and abs(py - ay) < epsilon:
            return min(ax, bx) - epsilon <= px <= max(ax, bx) + epsilon

        # Calculate the slope
        if abs(dx) > epsilon:
            m = dy / dx
            c = ay - m * ax
            # Check if the point satisfies the line equation y = mx + c within the epsilon
            return abs(py - (m * px + c)) < epsilon and min(ax, bx) - epsilon <= px <= max(ax, bx) + epsilon \
                and min(ay, by) - epsilon <= py <= max(ay, by) + epsilon
        return False

    def render_body(self):
        self.surface.fill((16, 16, 16))
        for i, plug in enumerate(self.plugs):
            pg.draw.circle(self.surface, plug.color, plug.position, self.PLUG_RADIUS)
            if plug.connection is not None:
                pg.draw.line(self.surface, plug.color, plug.position, self.sockets[plug.connection].position, 2)
        for socket in self.sockets:
            pg.draw.circle(self.surface, socket.color, socket.position, 4)

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            print("as")
            for plug in self.plugs:
                if self.point_on_plug(plug, (event.pos[0] - self.position[0], event.pos[1] - self.position[1])):

                    plug.connection = None
                    break
        super().handle_event(event)
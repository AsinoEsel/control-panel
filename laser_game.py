import pygame as pg
from math import sin, cos, acos, pi
from window_manager import Widget, Desktop
from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT, BACKGROUND_COLOR, DEFAULT_GAP
import random
import dmx
try:
    device_url = dmx.get_device_url()
except ValueError as e:
    if str(e) == 'No backend available':
        print("If you are on Windows, make sure to follow the pyftdi installation restructions (-> libusb-win32)")
else:
    dmx_universe = dmx.DMXUniverse(url=device_url) if device_url else None
        

def spherical_to_cartesian(phi, theta) -> pg.Vector3:
        return pg.Vector3(sin(theta) * cos(phi),
                          sin(theta) * sin(phi),
                          cos(theta))


class Camera:
    def __init__(self, zoom: float, shift: pg.Vector2 = pg.Vector2(0,0)) -> None:
        # Initial orientation facing 'forward' along the negative Z-axis
        self._yaw = pi/4
        self._pitch = pi/4
        self.position = spherical_to_cartesian(self._yaw, self._pitch)
        self.zoom = zoom
        self.shift = shift
    
    def project_point(self, point: pg.Vector3) -> pg.Vector2:
        from stl_renderer import find_basis_vectors
        camera_angle = -self.position
        basis_x, basis_y = find_basis_vectors(camera_angle)
        basis_x = pg.Vector3(basis_x[0], basis_x[1], basis_x[2])
        basis_y = pg.Vector3(basis_y[0], basis_y[1], basis_y[2])
        
        # Translate points relative to the camera position
        translated_point = point - self.position
        return pg.Vector2(self.zoom * translated_point.dot(basis_x) + self.shift.x,
                          - self.zoom * translated_point.dot(basis_y) + self.shift.y)
    
    @property
    def yaw(self):
        return self._yaw
    
    @yaw.setter
    def yaw(self, angle: float):
        self._yaw = angle
        self.position = spherical_to_cartesian(self._yaw, self._pitch)
    
    @property
    def pitch(self):
        return self._pitch
    
    @pitch.setter
    def pitch(self, angle: float):
        angle = max(min(angle, 0.99*pi), 0.01*pi)
        self._pitch = angle
        self.position = spherical_to_cartesian(self._yaw, self._pitch)


class Entity:
    def __init__(self, position: pg.Vector3) -> None:
        self.position = position
    
    def draw(self, surface: pg.Surface, camera: Camera):
        center = camera.project_point(self.position)
        pg.draw.circle(surface, (255,255,0), center, 4)


class Relay(Entity):
    def __init__(self, moving_head: dmx.MovingHead, position: pg.Vector3, orientation: pg.Vector3) -> None:
        super().__init__(position)
        self.orientation = orientation.normalize()
        self.moving_head = moving_head
        self.moving_head.pan = 1/2
        self._yaw = 3/2*pi
        self._pitch = 0
        self.beam_vector: pg.Vector3
        self.recalculate_beam_vector()
    
    def recalculate_beam_vector(self):
        self.beam_vector = spherical_to_cartesian(self.yaw, self.pitch)
    
    @property
    def yaw(self):
        return self._yaw
    
    @yaw.setter
    def yaw(self, yaw):
        self._yaw = yaw
        self.moving_head.pan = yaw / (3*pi)
        if self.moving_head.pan > 5/6:
            self.moving_head.pan -= 4/6
        elif self.moving_head.pan < 1/6:
            self.moving_head.pan += 4/6
        self.recalculate_beam_vector()
    
    @property
    def pitch(self):
        self.moving_head.tilt = self._pitch/pi + 1/2
        return self._pitch
    
    @pitch.setter
    def pitch(self, pitch):
        self._pitch = max(min(self.moving_head.theta_range[1], pitch), self.moving_head.theta_range[0])
        self.recalculate_beam_vector()
    
    def draw(self, surface: pg.Surface, camera: Camera):
        super().draw(surface, camera)
        center = camera.project_point(self.position)
        pg.draw.line(surface, (255,255,0), center, camera.project_point(self.position + 1.0*self.beam_vector), 2)


class Antenna(Entity):
    def __init__(self, position: pg.Vector3) -> None:
        super().__init__(position)
        self.active = False
    
    def draw(self, surface: pg.Surface, camera: Camera):
        center = camera.project_point(self.position)
        width = 0 if self.active else 2
        pg.draw.circle(surface, (255,255,0), center, 6, width)


class Viewport(Widget):
    def __init__(self, parent: Widget):
        super().__init__(parent, parent.position.x, parent.position.y, parent.surface.get_width(), parent.surface.get_height()//2)
        self.camera = Camera(zoom=64.0, shift=pg.Vector2(self.surface.get_width()//2, self.surface.get_height()//2))
        self.entities = []
    
    def update(self, tick: int, dt: int):
        rad_per_second = pi/4
        if self.active:
            radians = rad_per_second*dt/1000
            keys = pg.key.get_pressed()
            if keys[pg.K_LEFT]:
                self.camera.yaw += radians
            if keys[pg.K_RIGHT]:
                self.camera.yaw -= radians
            if keys[pg.K_UP]:
                self.camera.pitch -= radians
            if keys[pg.K_DOWN]:
                self.camera.pitch += radians
            if any((keys[pg.K_LEFT], keys[pg.K_RIGHT], keys[pg.K_UP], keys[pg.K_DOWN])):
                self.flag_as_needing_rerender()
    
    def render_origin(self):
        start = self.camera.project_point(pg.Vector3(0,0,0))
        end_x = self.camera.project_point(pg.Vector3(1,0,0))
        end_y = self.camera.project_point(pg.Vector3(0,1,0))
        end_z = self.camera.project_point(pg.Vector3(0,0,1))
        pg.draw.line(self.surface, (255,0,0), start, end_x)
        pg.draw.line(self.surface, (0,255,0), start, end_y)
        pg.draw.line(self.surface, (0,0,255), start, end_z)
    
    def draw_entities(self):
        for entity in self.entities:
            entity.draw(self.surface, self.camera)
    
    def render(self):
        self.surface.fill(BACKGROUND_COLOR)
        self.render_border()
        self.render_origin()
        self.draw_entities()
        

class LaserGame(Widget):
    def __init__(self, parent: Desktop, x=DEFAULT_GAP, y=DEFAULT_GAP, w=RENDER_WIDTH-2*DEFAULT_GAP, h=RENDER_HEIGHT-2*DEFAULT_GAP):
        super().__init__(parent, x, y, w, h)
        self.viewport = Viewport(self)
        self.elements.append(self.viewport)
        self.moving_heads = [moving_head := dmx.MovingHead("Moving Head", 1)]
        if dmx_universe:
            dmx_universe.add_device(moving_head)
            dmx_universe.start_dmx_thread()
        self.relays = [relay := Relay(moving_head=moving_head, position=pg.Vector3(0,0,0), orientation=pg.Vector3(1,0,0))]
        self.antennas = [Antenna(pg.Vector3.from_spherical((random.uniform(1,2), random.randrange(0,100), random.randrange(0,360)))),]
        self.selected_relay = relay
        self.viewport.entities = self.relays + self.antennas
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN and event.key == pg.K_i:
            self.selected_relay.moving_head.prism += 1
            print(self.selected_relay.moving_head.prism)
        return super().handle_event(event)
    
    def update(self, tick: int, dt: int):
        keys_pressed = pg.key.get_pressed()
        if keys_pressed[pg.K_a]:
            self.selected_relay.yaw += 0.005
        if keys_pressed[pg.K_d]:
            self.selected_relay.yaw -= 0.005
        if keys_pressed[pg.K_w]:
            self.selected_relay.pitch -= 0.005
        if keys_pressed[pg.K_s]:
            self.selected_relay.pitch += 0.005
        if any((keys_pressed[pg.K_a], keys_pressed[pg.K_d], keys_pressed[pg.K_w], keys_pressed[pg.K_s])):
            for antenna in self.antennas:
                for relay in self.relays:
                    vector_to_antenna = antenna.position - relay.position
                    angle = relay.beam_vector.angle_to(vector_to_antenna)
                    if angle <= 3:
                        antenna.active = True
                    else:
                        antenna.active = False
                
            self.viewport.flag_as_needing_rerender()
    
    def render(self) -> None:
        self.surface.fill(BACKGROUND_COLOR)
        self.blit_from_children()


if __name__ == "__main__":
    pg.mouse.set_visible(True)
    laser_game = LaserGame(parent=None)
    
    pg.init()
    laser_game.surface = pg.display.set_mode((RENDER_WIDTH,RENDER_HEIGHT))
    running = True
    clock = pg.time.Clock()
    dt = 0
    tick = 0

    while running:
        tick += 1
        
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False
            laser_game.handle_event(event)
        
        laser_game.propagate_update(tick, dt=dt)
        
        laser_game.render()
        
        pg.display.flip()
        pg.event.pump()
        dt = clock.tick(60)
import numpy as np
import quaternion
from stl import mesh, Dimension
from itertools import combinations


class Camera:
    def __init__(self, zoom: float = 1, shift: tuple[int, int] = (0, 0)):
        # Initial orientation facing 'forward' along the negative Z-axis
        self.orientation = quaternion.from_float_array([0, 0, 0, 1])
        self.zoom = zoom
        self.shift = shift
        self.pitch_angle = 0.0
        self.rotate_up_down(90)

    def get_cartesian_orientation_vector(self):
        # Convert quaternion to a direction vector
        forward_vector = quaternion.rotate_vectors(self.orientation, np.array([0, 0, -1]))
        return forward_vector

    def rotate_left_right(self, angle: float):
        # Convert angle from degrees to radians
        angle_rad = np.radians(angle)
        # Rotate around Z-axis
        z_axis = np.array([0, 0, 1])
        rotation = quaternion.from_rotation_vector(z_axis * angle_rad)
        self.orientation = rotation * self.orientation

    def rotate_up_down(self, angle: float):
        angle_rad = np.radians(angle)
        # Clamp the pitch angle to prevent flipping
        # Assuming epsilon is a small angle to prevent reaching the exact up or down
        epsilon = np.radians(1)  # For example, 5 degrees from the poles
        max_pitch = np.pi - epsilon  # Maximum pitch angle
        
        # Calculate new pitch angle and clamp it
        new_pitch = self.pitch_angle + angle_rad
        if new_pitch < epsilon:
            new_pitch = epsilon
        elif new_pitch > max_pitch:
            new_pitch = max_pitch

        # Calculate the angle difference to rotate
        delta_angle = new_pitch - self.pitch_angle
        self.pitch_angle = new_pitch  # Update the stored pitch angle

        # Rotate around X-axis
        x_axis = np.array([1, 0, 0])
        rotation = quaternion.from_rotation_vector(x_axis * delta_angle)
        self.orientation = self.orientation * rotation


def convert_stl_to_wireframe(file_path, camera: Camera):
    your_mesh = read_stl(file_path)
    unique_edges = extract_unique_edges(your_mesh)
    wireframe = project_to_2d(unique_edges, camera)
    return wireframe


def read_stl(file_path):
    # Load STL file
    your_mesh = mesh.Mesh.from_file(file_path)
    return your_mesh


def extract_unique_edges(your_mesh):
    # Extract unique edges from the mesh
    edges = []
    for face in your_mesh.vectors:
        for edge in combinations(face, 2):
            # Sort the vertices of the edge so that (point1, point2) is the same as (point2, point1)
            sorted_edge = tuple(sorted(edge, key=lambda x: (x[0], x[1], x[2])))
            edges.append(sorted_edge)
    return list(edges)


def project_to_2d(edges, camera: Camera):
    camera_position = camera.get_cartesian_orientation_vector()
    # Normalize the camera angle vector to ensure it's a unit vector
    camera_angle = normalize_vector(-camera_position)
    # Find two orthogonal vectors that are orthogonal to the camera angle
    """basis_x, basis_y = find_orthogonal_vectors(camera_angle)"""
    basis_x, basis_y = find_basis_vectors(camera_angle)
    
    # Translate points relative to the camera position
    translated_edges = [(edge - camera_position) for edge in edges]
    
    projected_edges = []
    for edge in translated_edges:
        projected_edge = []
        for point in edge:
            # After translating so camera is at origin, project the point onto the new basis vectors
            x = camera.zoom * np.dot(point, basis_x) + camera.shift[0]
            y = - camera.zoom * np.dot(point, basis_y) + camera.shift[1]
            projected_edge.append((x, y))
        projected_edges.append(projected_edge)
    return projected_edges


def normalize_vector(v):
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


def find_basis_vectors(normal):
    """
    Finds orthogonal basis vectors for the tangent plane at a point on the unit sphere,
    with the 'y' vector pointing 'up'.

    Parameters:
    - normal: np.ndarray, the normal vector at the point on the unit sphere.

    Returns:
    - A tuple of np.ndarrays: (x_vector, y_vector), where y_vector points 'up'.
    """
    # Ensure the normal vector is normalized
    N = normal / np.linalg.norm(normal)

    # Step 1: Choose an arbitrary vector A, considering the special case if N is parallel to Z-axis
    A = np.array([0, 0, 1]) if not np.allclose(N, [0, 0, 1], atol=1e-3) else np.array([1, 0, 0])

    # Step 2: Compute U = N x A
    U = np.cross(N, A)

    # Step 3: Compute V = N x U
    V = np.cross(N, U)

    # Normalize U and V
    U = U / np.linalg.norm(U)
    V = V / np.linalg.norm(V)

    # Correct V if its Z-component is negative to ensure it points "up"
    if V[2] < 0:
        V = -V

    return U, V


# find the max dimensions, so we can know the bounding box, getting the height,
# width, length (because these are the step size)...
def find_mins_maxs(obj):
    minx = maxx = miny = maxy = minz = maxz = None
    for p in obj.points:
        # p contains (x, y, z)
        if minx is None:
            minx = p[Dimension.X]
            maxx = p[Dimension.X]
            miny = p[Dimension.Y]
            minz = p[Dimension.Z]
            maxz = p[Dimension.Z]
            maxy = p[Dimension.Y]
        else:
            maxx = max(p[Dimension.X], maxx)
            minx = min(p[Dimension.X], minx)
            maxy = max(p[Dimension.Y], maxy)
            miny = min(p[Dimension.Y], miny)
            maxz = max(p[Dimension.Z], maxz)
            minz = min(p[Dimension.Z], minz)
    return minx, maxx, miny, maxy, minz, maxz


if __name__ == "__main__":
    import pygame as pg
    from window_manager_setup import RENDER_WIDTH, RENDER_HEIGHT, RENDER_SIZE
    
    file_path = 'media/fox_centered.stl'
    
    camera = Camera(zoom=4, shift=(RENDER_WIDTH//2, RENDER_HEIGHT//2))
        
    pg.init()
    screen = pg.display.set_mode(RENDER_SIZE)
    
    running = True
    clock = pg.time.Clock()
    while running:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False
        
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            camera.rotate_left_right(np.pi)
        if keys[pg.K_RIGHT]:
            camera.rotate_left_right(- np.pi)
        if keys[pg.K_UP]:
            camera.rotate_up_down(- np.pi)
        if keys[pg.K_DOWN]:
            camera.rotate_up_down(np.pi)

        
        wireframe = convert_stl_to_wireframe(file_path, camera)
        
        screen.fill((16,16,16))        
        for line_segment in wireframe:
            pg.draw.line(screen, (0,255,0), line_segment[0], line_segment[1])
                                
        pg.display.flip()
        pg.event.pump()
        clock.tick(60)
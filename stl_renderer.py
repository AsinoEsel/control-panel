import numpy as np
from stl import mesh
from itertools import combinations
from math import sin, cos, pi
import quaternion  # This library extends numpy with quaternion operations


"""class Camera:
    def __init__(self, phi: float = 0, theta: float = pi/2, zoom: float = 1, shift: tuple[int,int] = (0,0)) -> None:
        self.phi = phi
        self.theta = theta
        self.zoom = zoom
        self.shift = shift
    
    def get_cartesian_coordinates(self) -> np.array:
        return np.array([sin(self.theta)*cos(self.phi),
                         sin(self.theta)*sin(self.phi),
                         cos(self.theta)])"""

class Camera:
    def __init__(self, zoom: float = 1, shift: tuple[int, int] = (0, 0)) -> None:
        self.orientation = quaternion.quaternion(1, 0, 0, 0)  # No rotation
        self.zoom = zoom
        self.shift = shift

    def get_cartesian_coordinates(self) -> np.array:
        forward_vector = np.array([-1, 0, 0])  # Default forward vector
        rotated_vector = self.orientation * quaternion.quaternion(0, *forward_vector) * self.orientation.conjugate()
        return quaternion.as_float_array(rotated_vector)[1:]

    def rotate(self, axis: np.array, angle: float) -> None:
        q_rotation = quaternion.from_rotation_vector(axis * angle)
        self.orientation = q_rotation * self.orientation

    def rotate_left_right(self, angle: float) -> None:
        # Rotate around global Z-axis
        self.rotate(np.array([0, 0, 1]), angle)

    def rotate_up_down(self, angle: float) -> None:
        # Calculate camera's local X-axis for pitch rotation
        local_x_axis = quaternion.as_float_array(self.orientation * quaternion.quaternion(0, 1, 0, 0) * self.orientation.conjugate())[1:]
        self.rotate(local_x_axis, angle)

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

def convert_stl_to_wireframe(file_path, camera: Camera):
    your_mesh = read_stl(file_path)
    unique_edges = extract_unique_edges(your_mesh)
    wireframe = project_to_2d(unique_edges, camera)
    return wireframe

def normalize_vector(v):
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v

def find_orthogonal_vectors(normal):
    # Find a vector that is not parallel to the normal
    if abs(normal[0]) < abs(normal[2]):
        not_parallel = np.array([1, 0, 0])
    else:
        not_parallel = np.array([0, 0, 1])
    # Use the cross product to find two orthogonal vectors
    v1 = np.cross(normal, not_parallel)
    v2 = np.cross(normal, v1)
    return normalize_vector(v1), normalize_vector(v2)

def project_to_2d(edges, camera: Camera):
    camera_position = camera.get_cartesian_coordinates()
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


if __name__ == "__main__":
    import pygame as pg
    from setup import SCREEN_WIDTH, SCREEN_HEIGHT
    
    file_path = 'media/fox_centered.stl'
    # camera = Camera(phi=0, theta=pi/2, zoom=4, shift=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    camera = Camera(zoom=4, shift=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    running = True
    clock = pg.time.Clock()
    while running:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False
        
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            camera.rotate_left_right(np.pi / 100)
        if keys[pg.K_RIGHT]:
            camera.rotate_left_right(- np.pi / 100)
        if keys[pg.K_UP]:
            camera.rotate_up_down(- np.pi / 100)
        if keys[pg.K_DOWN]:
            camera.rotate_up_down(np.pi / 100)

        
        wireframe = convert_stl_to_wireframe(file_path, camera)
        
        screen.fill((16,16,16))        
        for line_segment in wireframe:
            pg.draw.line(screen, (0,255,0), line_segment[0], line_segment[1])
        
        # print(camera.orientation)
                        
        pg.display.flip()
        pg.event.pump()
        clock.tick(60)

import pygame as pg
from array import array
import moderngl
from window_manager_setup import RENDER_SIZE, QUARTER_RENDER_SIZE
from shaders_setup import shader_params
from debug_util import display_surface
import time

SHADER_LIST = ["Downscale", "Threshold", "Blur_H", "Blur_V", "Ghost", "Add", "CRT"]


class ShaderPipeline():
    def __init__(self, number_of_surfaces: int, texture_sizes: list[tuple[int,int]], shader_operations_todo: list[tuple[int, str, dict]], *, texture_filter = moderngl.LINEAR):
        self.number_of_surfaces = number_of_surfaces
        self.texture_sizes = texture_sizes
        self.shader_operations_todo = shader_operations_todo
        self.texture_filter = texture_filter
    
    def compile(self, surfaces: list[pg.Surface]) -> 'Shaders':
        if self.number_of_surfaces != len(surfaces):
            raise ValueError("Number of surfaces does not match the length of list of surfaces passed")
        
        ctx = moderngl.create_context(require=300)
        textures: list[moderngl.Texture] = []
        framebuffers: list[moderngl.Framebuffer] = []
        for i, surface in enumerate(surfaces):
            texture = ctx.texture(surface.get_size(), 4)
            texture.use(i)
            textures.append(texture)
            framebuffers.append(ctx.framebuffer(color_attachments=[texture]))
        for i, texture_size in enumerate(self.texture_sizes):
            texture = ctx.texture(texture_size, 4)
            texture.use(i + len(surfaces))
            textures.append(texture)
            framebuffers.append(ctx.framebuffer(color_attachments=[texture]))
        framebuffers.append(ctx.screen)
        
        programs: dict[str, moderngl.Program] = {}
        shader_operations = []
        for target_buffer, shader_name, uniforms in self.shader_operations_todo:
            if shader_name not in programs:
                program = get_shader_program(ctx, *shader_params[shader_name])
                programs[shader_name] = program
                shader_operations.append((target_buffer, program, uniforms))
            else:
                shader_operations.append((target_buffer, programs[shader_name], uniforms))
        
        quad_buffer_normal = ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 1.0,   # topleft
            1.0, 1.0, 1.0, 1.0,    # topright
            -1.0, -1.0, 0.0, 0.0,  # botleft
            1.0, -1.0, 1.0, 0.0,   # botright
        ]))
        
        quad_buffer_invert = ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 0.0,   # topleft
            1.0, 1.0, 1.0, 0.0,    # topright
            -1.0, -1.0, 0.0, 1.0,  # botleft
            1.0, -1.0, 1.0, 1.0,   # botright
        ]))
        
        vaos = []
        for i, (_, program, _) in enumerate(shader_operations):
            quad_buffer = quad_buffer_invert if i == len(shader_operations) - 1 else quad_buffer_normal                
            vaos.append(get_vertex_array(ctx, quad_buffer, program))
        
        return Shaders(surfaces, textures, framebuffers, shader_operations, vaos)
        

class Shaders:
    def __init__(self, surfaces: list[pg.Surface], textures: list[moderngl.Texture], framebuffers: list[moderngl.Framebuffer], shader_operations: list[tuple[int, moderngl.Program, dict]], vaos: list[moderngl.VertexArray]):
        self.surfaces_textures = [(surface, textures[i]) for i, surface in enumerate(surfaces)]
        self.framebuffers = framebuffers
        self.shader_operations = shader_operations
        self.vaos = vaos
    
    def activate(self):
        for i, (_, texture) in enumerate(self.surfaces_textures):
            texture.use(location=i)
        
    def apply(self, current_time: int):
        for surface, texture in self.surfaces_textures:
            texture.write(surface.get_view('1'))
        
        for i, (target_buffer, program, uniforms) in enumerate(self.shader_operations):
            for uniform, value in uniforms.items():
                program[uniform] = value
            self.framebuffers[target_buffer].use()
            self.vaos[i].render(mode=moderngl.TRIANGLE_STRIP)
                
def get_context() -> moderngl.Context:
    return moderngl.create_context(require=300)

def get_shader_program(ctx: moderngl.Context, vert_shader_path: str, frag_shader_path: str, shader_parameters: dict[str, int|float]) -> moderngl.Program:
    with open(vert_shader_path) as v: vert_shader = v.read()
    with open(frag_shader_path) as f: frag_shader = f.read()
    program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
    for name, value in shader_parameters.items():
        program[name] = value
    return program

def get_vertex_array(ctx: moderngl.Context, quad_buffer: moderngl.Buffer, program: moderngl.Program) -> moderngl.VertexArray:
    return ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])

def main(fullscreen: bool = False):
    pg.init()
    flags = pg.OPENGL | pg.DOUBLEBUF
    if fullscreen:
        flags |= pg.FULLSCREEN
    pg.display.set_mode(RENDER_SIZE, flags=flags)
    
    display = pg.Surface(RENDER_SIZE)
    
    shaders = Shaders(texture_sizes=[RENDER_SIZE, QUARTER_RENDER_SIZE, QUARTER_RENDER_SIZE],
                      surfaces_ints=[(display, 0)],
                      shader_operations_todo=[(1, "Downscale", {"_MainTex": 0}),
                                              (1, "Threshold", {"_MainTex": 1}),
                                              (1, "Blur_H", {"_MainTex": 1}),
                                              (1, "Blur_V", {"_MainTex": 1}),
                                              (2, "Ghost", {"_MainTex": 1, "_SecondaryTex": 2}),
                                              (0, "Add", {"_MainTex": 0, "_SecondaryTex": 2}),
                                              (0, "CRT", {"_MainTex": 0}),
                                              (-1, "To_BGRA", {"_MainTex": 0}),
                                              ])
    
    shaders.compile_shaders()

    clock = pg.time.Clock()

    while True:
        current_time = time.time()
        
        for event in pg.event.get():
            if event.type == pg.KEYDOWN or event.type == pg.QUIT:
                pg.quit()
        
        # pygame rendering
        display.fill((0,0,0))
        img = pg.image.load("media/screenshot_downscaled.png")
        display.blit(pg.transform.scale(img, RENDER_SIZE), (0,0))
        
        # modernGL
        shaders.apply(current_time=current_time)
        
        pg.display.flip()        
        clock.tick(60)


if __name__ == '__main__':
    main(fullscreen=False)
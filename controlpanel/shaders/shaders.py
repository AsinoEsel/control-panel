import pygame as pg
from array import array
import moderngl
# from controlpanel.scripts.gui.window_manager.window_manager_setup import RENDER_SIZE, QUARTER_RENDER_SIZE
from .shader_manifest import shader_params


class Shaders:
    def __init__(self, texture_sizes: list[tuple[int, int]], shader_operations: list[tuple[int, str, dict]], *, texture_filter=moderngl.LINEAR):
        self.ctx: moderngl.Context = moderngl.create_context(require=300)
        self.textures: list[moderngl.Texture] = [self.ctx.texture(texture_size, 4) for texture_size in texture_sizes]
        self.framebuffers: list[moderngl.Framebuffer] = []
        for loc, texture in enumerate(self.textures):
            texture.filter = (texture_filter, texture_filter)
            texture.use(loc)
            self.framebuffers.append(self.ctx.framebuffer(color_attachments=[texture]))
        self.framebuffers.append(self.ctx.screen)
        programs: dict[str, moderngl.Program] = {}
        self.shader_operations: list[tuple[int, moderngl.Program, dict]] = []
        for target_buffer, shader_name, uniforms in shader_operations:
            if shader_name not in programs:
                program = get_shader_program(self.ctx, *shader_params[shader_name])
                programs[shader_name] = program
                self.shader_operations.append((target_buffer, program, uniforms))
            else:
                self.shader_operations.append((target_buffer, programs[shader_name], uniforms))
        
        quad_buffer_normal = self.ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 1.0,   # top-left
            1.0, 1.0, 1.0, 1.0,    # top-right
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            1.0, -1.0, 1.0, 0.0,   # bottom-right
        ]))
        
        quad_buffer_invert = self.ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 0.0,   # top-left
            1.0, 1.0, 1.0, 0.0,    # top-right
            -1.0, -1.0, 0.0, 1.0,  # bottom-left
            1.0, -1.0, 1.0, 1.0,   # bottom-right
        ]))
        
        self.vaos: list[moderngl.VertexArray] = []
        for i, (_, program, _) in enumerate(self.shader_operations):
            quad_buffer = quad_buffer_invert if i == len(self.shader_operations) - 1 else quad_buffer_normal                
            self.vaos.append(get_vertex_array(self.ctx, quad_buffer, program))
                
    def apply(self, surfaces: list[pg.Surface], current_time: float = 0.0):

        for i, surface in enumerate(surfaces):
            self.textures[i].write(surface.get_view('1'))
        
        for i, (target_buffer, program, uniforms) in enumerate(self.shader_operations):
            for uniform, value in uniforms.items():
                program[uniform] = value
            self.framebuffers[target_buffer].use()
            self.vaos[i].render(mode=moderngl.TRIANGLE_STRIP)
                

def get_shader_program(ctx: moderngl.Context, vert_shader_path: str, frag_shader_path: str, shader_parameters: dict[str: int | float]) -> moderngl.Program:
    with open(vert_shader_path) as v:
        vert_shader = v.read()
    with open(frag_shader_path) as f:
        frag_shader = f.read()
    program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
    for name, value in shader_parameters.items():
        program[name] = value
    return program


def get_vertex_array(ctx: moderngl.Context, quad_buffer: moderngl.Buffer, program: moderngl.Program) -> moderngl.VertexArray:
    return ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])


# def main(fullscreen: bool = False):
#     pg.init()
#     flags = pg.OPENGL | pg.DOUBLEBUF
#     if fullscreen:
#         flags |= pg.FULLSCREEN
#     pg.display.set_mode(RENDER_SIZE, flags=flags)
#
#     display = pg.Surface(RENDER_SIZE)
#
#     shaders = Shaders(texture_sizes=[RENDER_SIZE, QUARTER_RENDER_SIZE, QUARTER_RENDER_SIZE],
#                       shader_operations=[(1, "Downscale", {"_MainTex": 0}),
#                                          (1, "Threshold", {"_MainTex": 1}),
#                                          (1, "Blur_H", {"_MainTex": 1}),
#                                          (1, "Blur_V", {"_MainTex": 1}),
#                                          (2, "Ghost", {"_MainTex": 1, "_SecondaryTex": 2}),
#                                          (0, "Add", {"_MainTex": 0, "_SecondaryTex": 2}),
#                                          (0, "CRT", {"_MainTex": 0}),
#                                          (-1, "To_BGRA", {"_MainTex": 0}),
#                                          ])
#
#     clock = pg.time.Clock()
#
#     while True:
#         current_time = time.time()
#
#         for event in pg.event.get():
#             if event.type == pg.KEYDOWN or event.type == pg.QUIT:
#                 pg.quit()
#
#         # pygame rendering
#         display.fill((0, 0, 0))
#         img = pg.image.load("controlpanel/gui/media/screenshot_downscaled.png")
#         display.blit(pg.transform.scale(img, RENDER_SIZE), (0, 0))
#
#         # modernGL
#         shaders.apply([display,], current_time=current_time)
#
#         pg.display.flip()
#         clock.tick(60)
#
#
# if __name__ == '__main__':
#     main(fullscreen=False)

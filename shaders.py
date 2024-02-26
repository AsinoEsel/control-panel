import pygame as pg
from array import array
import moderngl
from window_manager_setup import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_SIZE
from shaders_setup import shader_params
from debug_util import display_surface
import time

SHADER_LIST = ["Downscale", "Threshold", "Blur_H", "Blur_V", "Add", "CRT"]

class Shaders:
    def __init__(self, shaders: list[str], *, texture_filter: int = moderngl.LINEAR):
        self.ctx = get_context()
        
        quad_buffer_invert = self.ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 0.0,   # topleft
            1.0, 1.0, 1.0, 0.0,    # topright
            -1.0, -1.0, 0.0, 1.0,  # botleft
            1.0, -1.0, 1.0, 1.0,   # botright
        ]))
        quad_buffer = self.ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 1.0,   # topleft
            1.0, 1.0, 1.0, 1.0,    # topright
            -1.0, -1.0, 0.0, 0.0,  # botleft
            1.0, -1.0, 1.0, 0.0,   # botright
        ]))
        
        self.programs: dict[str:moderngl.Program] = {shader: get_shader_program(self.ctx, *shader_params[shader]) for shader in shaders}
        self.vaos: list[moderngl.VertexArray] = [get_vertex_array(self.ctx, quad_buffer, program) for program in self.programs.values()]
        self.final_vao = get_vertex_array(self.ctx, quad_buffer_invert, get_shader_program(self.ctx, *shader_params["To_BGRA"]))
        
        self.texture = self.ctx.texture((SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 4)
        self.texture.filter = (texture_filter, texture_filter)
        self.texture.use(location=0)
        self.texture2 = self.ctx.texture(SCREEN_SIZE, 4)
        self.texture2.filter = (texture_filter, texture_filter)
        self.texture2.use(location=1)
        
        self.fbo = self.ctx.framebuffer(color_attachments=[self.texture])
        self.fbo2 = self.ctx.framebuffer(color_attachments=[self.texture2])
    
    def apply(self, surface: pg.Surface, current_time: int):
        self.texture2.write(surface.get_view('1'))
        
        self.fbo.use()
        for vao in self.vaos[0:4]:
            vao.render(mode=moderngl.TRIANGLE_STRIP)
        self.fbo2.use()
        for vao in self.vaos[4:]:
            vao.render(mode=moderngl.TRIANGLE_STRIP)
        if crt_program := self.programs.get('CRT'):
            crt_program['_ScanlineY'] = current_time / 5 - int(current_time / 5)
        self.ctx.screen.use()
        self.final_vao.render(mode=moderngl.TRIANGLE_STRIP)
        
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
    pg.display.set_mode(SCREEN_SIZE, flags=flags)
    
    display = pg.Surface(SCREEN_SIZE)
    shaders = Shaders(SHADER_LIST)

    clock = pg.time.Clock()

    while True:
        current_time = time.time()
        
        for event in pg.event.get():
            if event.type == pg.KEYDOWN or event.type == pg.QUIT:
                pg.quit()
        
        # pygame rendering
        display.fill((0,0,0))
        img = pg.image.load("media/screenshot_downscaled.png")
        display.blit(pg.transform.scale(img, SCREEN_SIZE), (0,0))
        
        # modernGL
        shaders.apply(display, current_time=current_time)
        
        pg.display.flip()        
        clock.tick(60)


if __name__ == '__main__':
    main(fullscreen=True)
import pygame as pg
from array import array
import moderngl
from window_manager_setup import SCREEN_HEIGHT, SCREEN_SIZE
from shaders_setup import shader_params
import time

SHADER_LIST = ["Threshold", "Blur_H", "Blur_V", "Add", "CRT"]

class Shaders:
    def __init__(self, shaders: list[str]):
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
        self.programs: list[moderngl.Program] = [get_shader_program(self.ctx, *shader_params[shader]) for shader in shaders]
        self.vaos = [get_vertex_array(self.ctx, quad_buffer, program) for program in self.programs]
        self.final_vao = get_vertex_array(self.ctx, quad_buffer_invert, get_shader_program(self.ctx, *shader_params["Nothing"]))
        self.texture = self.ctx.texture(SCREEN_SIZE, 4)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture.use(location=0)
        self.texture2 = self.ctx.texture(SCREEN_SIZE, 4)
        self.texture2.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture2.use(location=1)
        self.fbo = self.ctx.framebuffer(color_attachments=[self.texture])
    
    def apply(self, surface: pg.Surface):
        self.texture.write(surface.get_view('1'))
        self.texture2.write(surface.get_view('1'))
        
        self.fbo.use()
        for vao in self.vaos:
            vao.render(mode=moderngl.TRIANGLE_STRIP)
        # program_crt['_ScanlineY'] = current_time / 5 - int(current_time / 5)
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


def surf_to_texture(surf: pg.Surface, ctx: moderngl.Context) -> moderngl.Texture:
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    tex.write(surf.get_view('1'))
    return tex


def create_framebuffer(ctx: moderngl.Context, width: int, height: int) -> tuple[moderngl.Framebuffer, moderngl.Texture]:
    texture = ctx.texture((width, height), 4)
    texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
    framebuffer = ctx.framebuffer(color_attachments=[texture])
    return framebuffer, texture


def main():
    pg.init()
    screen = pg.display.set_mode(SCREEN_SIZE, pg.OPENGL | pg.DOUBLEBUF)
    display = pg.Surface(SCREEN_SIZE)
    
    """ctx = get_context()
    
    quad_buffer = ctx.buffer(data=array('f', [
        -1.0, 1.0, 0.0, 0.0,   # topleft
        1.0, 1.0, 1.0, 0.0,    # topright
        -1.0, -1.0, 0.0, 1.0,  # botleft
        1.0, -1.0, 1.0, 1.0,   # botright
    ]))
    
    quad_buffer2 = ctx.buffer(data=array('f', [
        -1.0, 1.0, 0.0, 1.0,   # topleft
        1.0, 1.0, 1.0, 1.0,    # topright
        -1.0, -1.0, 0.0, 0.0,  # botleft
        1.0, -1.0, 1.0, 0.0,   # botright
    ]))
    
    texture = ctx.texture(SCREEN_SIZE, 4)
    texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
    texture.use(location=0)
    texture2 = ctx.texture(SCREEN_SIZE, 4)
    texture2.filter = (moderngl.LINEAR, moderngl.LINEAR)
    texture2.use(location=1)
    
    program_crt = get_shader_program(ctx, *shader_params["CRT"])
    program_threshold = get_shader_program(ctx, *shader_params["Threshold"])
    program_blur_h = get_shader_program(ctx, *shader_params["Blur_H"])
    program_blur_v = get_shader_program(ctx, *shader_params["Blur_V"])
    program_add = get_shader_program(ctx, *shader_params["Add"])
    program_nothing = get_shader_program(ctx, *shader_params["Nothing"])
    
    fbo_texture = ctx.framebuffer(color_attachments=[texture])
    
    vao_threshold = get_vertex_array(ctx, quad_buffer2, program_threshold)
    vao_blur_h = get_vertex_array(ctx, quad_buffer2, program_blur_h)
    vao_blur_v = get_vertex_array(ctx, quad_buffer2, program_blur_v)
    vao_add = get_vertex_array(ctx, quad_buffer2, program_add)
    vao_crt = get_vertex_array(ctx, quad_buffer2, program_crt)
    vao_to_screen = get_vertex_array(ctx, quad_buffer, program_nothing)"""
    
    shaders = Shaders(["Threshold", "Blur_H", "Blur_V", "Add", "CRT"])

    clock = pg.time.Clock()
    img = pg.image.load("media/screenshot.png")

    while True:
        current_time = time.time()
        
        for event in pg.event.get():
            if event.type == pg.KEYDOWN or event.type == pg.QUIT:
                pg.quit()
        
        # pygame rendering
        display.fill((0,0,0))
        display.blit(pg.transform.scale(img, SCREEN_SIZE), (0,0))
        
        # modernGL
        shaders.apply(display)
        """texture.write(display.get_view('1'))
        texture2.write(display.get_view('1'))

        fbo_texture.use()
        vao_threshold.render(mode=moderngl.TRIANGLE_STRIP)
        vao_blur_h.render(mode=moderngl.TRIANGLE_STRIP)
        vao_blur_v.render(mode=moderngl.TRIANGLE_STRIP)
        vao_add.render(mode=moderngl.TRIANGLE_STRIP)
        program_crt['_ScanlineY'] = current_time / 5 - int(current_time / 5)
        vao_crt.render(mode=moderngl.TRIANGLE_STRIP)
        
        ctx.screen.use()
        vao_to_screen.render(mode=moderngl.TRIANGLE_STRIP)"""
        
        pg.display.flip()        
        clock.tick(60)


if __name__ == '__main__':
    main()
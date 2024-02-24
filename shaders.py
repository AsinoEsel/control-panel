import pygame as pg
from array import array
import moderngl
from window_manager_setup import SCREEN_WIDTH, SCREEN_HEIGHT

TRIANGLE_STRIP = moderngl.TRIANGLE_STRIP

def get_context() -> moderngl.Context:
    return moderngl.create_context(require=300)

def get_shader_program(ctx: moderngl.Context) -> moderngl.Program:
    with open("shaders/quad_vertex_shader300es.vert") as v: vert_shader = v.read()
    with open("shaders/crt_fragment_shader300es.frag") as f: frag_shader = f.read()
    program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
    program['_MainTex'] = 0
    program['_Curvature'] = 8.0
    program['_VignetteWidth'] = 40.0
    program['_ScreenParams'] = (SCREEN_WIDTH, SCREEN_HEIGHT)
    return program


def get_render_object(ctx: moderngl.Context) -> moderngl.VertexArray:
    quad_buffer = ctx.buffer(data=array('f', [
        # position (x, y), uv coords (x, y)
        -1.0, 1.0, 0.0, 0.0,   # topleft
        1.0, 1.0, 1.0, 0.0,    # topright
        -1.0, -1.0, 0.0, 1.0,  # botleft
        1.0, -1.0, 1.0, 1.0,   # botright
    ]))
    program = get_shader_program(ctx)
    return ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])


def surf_to_texture(surf: pg.Surface, ctx: moderngl.Context) -> moderngl.Texture:
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex


def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.OPENGL | pg.DOUBLEBUF)
    display = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    ctx = get_context()
    render_object = get_render_object(ctx)
    frame_tex = surf_to_texture(display, ctx)
    frame_tex.use(0)
    
    clock = pg.time.Clock()
    img = pg.image.load("media/screenshot.png")
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
        
        # pygame rendering
        display.fill((0,0,0))
        display.blit(pg.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0,0))
        
        # openGL rendering
        frame_tex.write(display.get_view('1'))
        render_object.render(mode=moderngl.TRIANGLE_STRIP)
        
        pg.display.flip()        
        clock.tick(60)


if __name__ == '__main__':
    main()
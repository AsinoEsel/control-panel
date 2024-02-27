from window_manager_setup import RENDER_SIZE, RENDER_HEIGHT

crt_shader_uniforms = {
    '_MainTex': 0,
    '_Curvature': 8.0,
    '_VignetteWidth': 40.0,
    '_ScreenParams': RENDER_SIZE,
    '_ScanlineHeight': 2.0 / RENDER_HEIGHT,
}

threshold_shader_uniforms = {
    '_MainTex': 1,
    '_LuminanceThreshold': 0.07,
}

blur_shader_uniforms = {
    '_MainTex': 1,
    '_Sigma': (sigma:=10),
    'u_resolution': RENDER_SIZE,
    '_KernelSize': 4*sigma+1,
}

add_shader_uniforms = {
    '_MainTex': 0,
    '_SecondaryTex': 1,
    '_Influence': (2.0, 1.0, 1.0, 0.0),
}

to_bgra_uniforms = {
    '_MainTex': 0,
}

downscale_uniforms = {
    '_MainTex': 0,
}

shader_params: dict[str: tuple[str, str, dict]] = {
    "CRT": ("shaders/quad.vert", "shaders/crt.frag", crt_shader_uniforms),
    "Threshold": ("shaders/quad.vert", "shaders/threshold.frag", threshold_shader_uniforms),
    "Blur_H": ("shaders/quad.vert", "shaders/blur_h.frag", blur_shader_uniforms),
    "Blur_V": ("shaders/quad.vert", "shaders/blur_v.frag", blur_shader_uniforms),
    "Add": ("shaders/quad.vert", "shaders/add.frag", add_shader_uniforms),
    "To_BGRA": ("shaders/quad.vert", "shaders/to_bgra.frag", to_bgra_uniforms),
    "Downscale": ("shaders/quad.vert", "shaders/downscale.frag", downscale_uniforms),
}

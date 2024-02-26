from window_manager_setup import SCREEN_SIZE, SCREEN_HEIGHT

crt_shader_uniforms = {
    '_MainTex': 0,
    '_Curvature': 8.0,
    '_VignetteWidth': 40.0,
    '_ScreenParams': SCREEN_SIZE,
    '_ScanlineHeight': 2.0 / SCREEN_HEIGHT,
}

threshold_shader_uniforms = {
    '_MainTex': 0,
    '_LuminanceThreshold': 0.1,
}

blur_shader_uniforms = {
    '_MainTex': 0,
    '_Sigma': 12,
    'u_resolution': SCREEN_SIZE,
    '_KernelSize': 25,
}

add_shader_uniforms = {
    '_MainTex': 0,
    '_SecondaryTex': 1,
    '_Influence': 1.0,
}

shader_params: dict[str: tuple[str, str, dict]] = {
    "CRT": ("shaders/quad.vert", "shaders/crt.frag", crt_shader_uniforms),
    "Threshold": ("shaders/quad.vert", "shaders/threshold.frag", threshold_shader_uniforms),
    "Blur_H": ("shaders/quad.vert", "shaders/blur_h.frag", blur_shader_uniforms),
    "Blur_V": ("shaders/quad.vert", "shaders/blur_v.frag", blur_shader_uniforms),
    "Add": ("shaders/quad.vert", "shaders/add.frag", add_shader_uniforms),
    "Nothing": ("shaders/quad.vert", "shaders/to_bgra.frag", {}),
}
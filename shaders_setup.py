from window_manager_setup import RENDER_SIZE, RENDER_HEIGHT

downscale_uniforms = {
    '_MainTex': 0,
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

ghost_shader_uniforms = {
    '_MainTex': 1,
    '_SecondaryTex': 2,
    '_FadeIntensity': 0.6,
    '_GhostInfluence': 0.9,
}

add_shader_uniforms = {
    '_MainTex': 0,
    '_SecondaryTex': 2,
    '_Influence': (1.0, .25, .25, 0.0), # TODO: Does this do anything?
    #'_Influence': (2.0, 1.0, 1.0, 0.0),
}

crt_shader_uniforms = {
    '_MainTex': 0,
    '_Curvature': 8.0,
    '_VignetteWidth': 40.0,
    '_ScreenParams': RENDER_SIZE,
    '_ScanlineHeight': 2.0 / RENDER_HEIGHT,
    '_ScanlineStrength': 1.2,
}

to_bgra_uniforms = {
    '_MainTex': 0,
}

shader_params: dict[str: tuple[str, str, dict]] = {
    "Downscale": ("shaders/quad.vert", "shaders/downscale.frag", downscale_uniforms),
    "Threshold": ("shaders/quad.vert", "shaders/threshold.frag", threshold_shader_uniforms),
    "Blur_H": ("shaders/quad.vert", "shaders/blur_h.frag", blur_shader_uniforms),
    "Blur_V": ("shaders/quad.vert", "shaders/blur_v.frag", blur_shader_uniforms),
    "Ghost": ("shaders/quad.vert", "shaders/ghost.frag", ghost_shader_uniforms),
    "Add": ("shaders/quad.vert", "shaders/add.frag", add_shader_uniforms),
    "CRT": ("shaders/quad.vert", "shaders/crt.frag", crt_shader_uniforms),
    "To_BGRA": ("shaders/quad.vert", "shaders/to_bgra.frag", to_bgra_uniforms),
}

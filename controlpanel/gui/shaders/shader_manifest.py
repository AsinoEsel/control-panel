"""
This module defines all available shaders and their uniforms
"""


from controlpanel.gui.window_manager.window_manager_setup import RENDER_SIZE, RENDER_HEIGHT

downscale_uniforms = {
    '_MainTex': 0,
}

threshold_shader_uniforms = {
    '_MainTex': 1,
    '_LuminanceThreshold': 0.07,
}

blur_shader_uniforms = {
    '_MainTex': 1,
    '_Sigma': (sigma := 10),
    'u_resolution': RENDER_SIZE,
    '_KernelSize': 4*sigma+1,
}

ghost_shader_uniforms = {
    '_MainTex': 1,
    '_SecondaryTex': 2,
    '_NewIntensity': 0.6,
    '_GhostInfluence': 0.9,
}

add_shader_uniforms = {
    '_MainTex': 0,
    '_SecondaryTex': 2,
    '_Influence': (.25, .25, .25, 0.0), # TODO: Does this do anything?
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
    "Downscale": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/downscale.frag", downscale_uniforms),
    "Threshold": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/threshold.frag", threshold_shader_uniforms),
    "Blur_H": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/blur_h.frag", blur_shader_uniforms),
    "Blur_V": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/blur_v.frag", blur_shader_uniforms),
    "Ghost": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/ghost.frag", ghost_shader_uniforms),
    "Add": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/add.frag", add_shader_uniforms),
    "CRT": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/crt.frag", crt_shader_uniforms),
    "To_BGRA": ("controlpanel/gui/shaders/quad.vert", "controlpanel/gui/shaders/to_bgra.frag", to_bgra_uniforms),
}

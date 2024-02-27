#version 300 es

precision mediump float;

// Texture samplers for the two input textures
uniform sampler2D _MainTex;
uniform sampler2D _SecondaryTex;
uniform float _FadeIntensity;
uniform float _GhostInfluence;

// The texture coordinate for this fragment, interpolated from the vertices
in vec2 uvs;

// Output color of the fragment
out vec4 color;

void main()
{
    // Sample the pixel color from each texture
    vec4 color1 = texture(_MainTex, uvs);
    vec4 color2 = texture(_SecondaryTex, uvs);

    //Fade
    color2 *= _FadeIntensity;

    // Add the colors together
    color1 += _GhostInfluence * color2;

    // Clamp and output
    color = clamp(color1, 0.0, 1.0);
}

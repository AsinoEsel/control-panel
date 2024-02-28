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
    vec4 newColor = texture(_MainTex, uvs);
    vec4 ghostColor = texture(_SecondaryTex, uvs);

    //Fade
    ghostColor *= _GhostInfluence;

    // Add the colors together
    newColor = _FadeIntensity * newColor + ghostColor;

    // Clamp and output
    color = clamp(newColor, 0.0, 1.0);
}

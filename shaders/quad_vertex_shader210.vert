#version 120 // OpenGL 2.1 uses GLSL 1.20

// Use 'attribute' for input vertex attributes
attribute vec2 vert;
attribute vec2 texcoord;

// Use 'varying' to pass data to the fragment shader
varying vec2 uvs;

void main() {
    uvs = texcoord;
    gl_Position = vec4(vert, 0.0, 1.0);
}
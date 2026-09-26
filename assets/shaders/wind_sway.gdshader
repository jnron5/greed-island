shader_type canvas_item;
// Sea breeze for plants (palms, trees, grass tufts): each row of the sprite is
// shifted sideways by whole texels, more toward the top, so the trunk stays
// rooted and the crown leans and bobs. A steady lean plus a sway that swells
// in slow gusts; the phase comes from the node's world position so
// neighbouring plants move together like a wave, not in lockstep.
// Sprites need a few transparent columns either side for the crown to move into.

uniform float lean = 1.0;          // steady lean at the top, in texels
uniform float sway = 2.0;          // extra swing at the top in a gust, in texels
uniform float speed = 1.4;
uniform float bend = 1.8;          // >1: the bend gathers near the top
uniform float root = 0.0;          // fraction of the height (from the bottom) that never moves

varying float phase;
varying vec4 tint;

void vertex() {
	vec2 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xy;
	phase = origin.x * 0.004 + origin.y * 0.0015;
	tint = COLOR;
}

void fragment() {
	float h = pow(clamp((1.0 - UV.y - root) / (1.0 - root), 0.0, 1.0), bend);
	float gust = 0.55 + 0.45 * sin(TIME * 0.33 - phase * 9.0);
	float t = TIME * speed - phase * 6.2832;
	float swing = sin(t) * 0.7 + sin(t * 2.3 + 1.3) * 0.3;
	float dx = floor(h * (lean * gust + sway * gust * swing) + 0.5);
	COLOR = texture(TEXTURE, UV - vec2(dx * TEXTURE_PIXEL_SIZE.x, 0.0)) * tint;
}

shader_type canvas_item;
// Wind over a zone's ground image. surface_map is the same size as the ground:
// red marks grass (and crops), which ripples as gusts roll across it: along
// each wave crest the blades are drawn one texel downwind and catch a little
// light, like grass bending over. Everything else is drawn as is.

uniform sampler2D surface_map : filter_nearest;
uniform vec2 wind_dir = vec2(1.0, 0.3);
uniform float strength = 1.0;

varying vec4 tint;

void vertex() {
	tint = COLOR;
}

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	vec2 texel = TEXTURE_PIXEL_SIZE;
	vec2 px = floor(UV / texel);                 // whole texels keep the pixel art crisp
	float grass = step(0.5, texture(surface_map, UV).r);
	vec2 dir = normalize(wind_dir);
	float along = dot(px, dir);
	float drift = noise(px * 0.012 + vec2(TIME * 0.1, 0.0)) * 5.0;
	float wave = sin(along * 0.05 - TIME * 1.8 + drift);
	// Gusts: broad patches that sweep downwind; calm between them.
	float gust = smoothstep(0.35, 0.8, noise(px * 0.005 - dir * TIME * 0.12));
	float crest = smoothstep(0.45, 0.95, wave) * gust * strength;
	vec2 shifted = UV - vec2(texel.x * step(0.5, crest), 0.0);
	float grass_there = step(0.5, texture(surface_map, shifted).r);
	vec4 c = texture(TEXTURE, mix(UV, shifted, grass * grass_there));
	c.rgb += grass * crest * vec3(0.05, 0.065, 0.02);
	COLOR = c * tint;
}

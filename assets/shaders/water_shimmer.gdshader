shader_type canvas_item;
// Moving light sparkles on water. Drawn over the zone's ground; the level map
// masks it to sea cells (red channel 0 = level 0 = water).

uniform sampler2D level_map : filter_nearest;
uniform vec2 map_cells;          // level map size in cells
uniform float strength = 0.35;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	float water = step(texture(level_map, UV).r, 0.05);
	vec2 p = UV * map_cells * 2.0;
	float t = TIME * 0.6;
	float n = noise(p + vec2(t, t * 0.4)) * noise(p * 1.7 - vec2(t * 0.7, -t * 0.3));
	float sparkle = smoothstep(0.42, 0.62, n);
	float swell = noise(p * 0.35 + vec2(t * 0.2, 0.0)) * 0.12;
	COLOR = vec4(0.85, 1.0, 1.0, (sparkle * strength + swell) * water);
}

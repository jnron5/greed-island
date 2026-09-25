shader_type canvas_item;
// Moving light sparkles on water. Drawn over the zone's ground; the level map
// masks it to sea cells (red channel 0 = level 0 = water; green marks dry
// sea-level ground such as beaches and docks, which stays still).

uniform sampler2D level_map : filter_nearest;
uniform vec2 map_cells;          // level map size in cells
uniform float strength = 0.5;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	vec4 cell = texture(level_map, UV);
	float water = step(cell.r, 0.05) * (1.0 - step(0.5, cell.g));
	vec2 p = UV * map_cells * 7.0;   // fine glints, a few pixels each
	float t = TIME * 0.6;
	float n = noise(p + vec2(t, t * 0.4)) * noise(p * 1.7 - vec2(t * 0.7, -t * 0.3));
	float sparkle = smoothstep(0.55, 0.66, n);
	float swell = noise(p * 0.08 + vec2(t * 0.2, 0.0)) * 0.06;
	COLOR = vec4(0.85, 1.0, 1.0, (sparkle * strength + swell) * water);
}

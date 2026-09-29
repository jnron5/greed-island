shader_type canvas_item;
// Night colour grade over the whole outdoor view (scripts/world/night_grade.gd). A plain
// darker tint only looks like the brightness was turned down; real night drains colour
// out of everything the lamps don't reach, shifts it toward moonlit blue and deepens the
// shadows, while lamp-lit pools keep their warm colour. `night` is 0 by day, 1 at night.

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float night : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	float lum = dot(c, vec3(0.299, 0.587, 0.114));
	// How much a pixel is lit by a lamp: warm and bright pixels are, cold dim ones aren't.
	float warmth = clamp((c.r - c.b) * 2.0, 0.0, 1.0);
	float lit = clamp(smoothstep(0.3, 0.62, lum) + warmth * smoothstep(0.18, 0.4, lum), 0.0, 1.0);
	vec3 moon = vec3(lum) * vec3(0.6, 0.76, 1.18);
	vec3 graded = mix(c, moon, night * 0.7 * (1.0 - lit));
	graded *= mix(1.0, 0.78 + 0.3 * lit, night);
	// Moonlight catches the brightest cold surfaces (water sparkle, pale stone) a little.
	graded += vec3(0.02, 0.035, 0.07) * night * smoothstep(0.25, 0.5, lum) * (1.0 - warmth);
	vec2 d = SCREEN_UV - 0.5;
	graded *= 1.0 - dot(d, d) * 1.1 * night;
	COLOR = vec4(graded, 1.0);
}

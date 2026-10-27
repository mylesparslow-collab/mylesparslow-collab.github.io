/* Shader backdrops for the appearance panel, adapted from Specimen Room's Gradients & Shaders cabinet.
   Loaded only when a visitor picks one. Each entry is a GLSL ES 1.0 fragment body and its four palette colours. */
(function () {
  'use strict';
  var PRE = [
    'precision highp float;',
    'uniform float u_time; uniform vec2 u_res; uniform vec3 u_c1, u_c2, u_c3, u_c4;',
    'float hash21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }',
    'vec2 hash22(vec2 p){ float n = hash21(p); return vec2(n, hash21(p + n + 19.19)); }',
    'float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);',
    '  return mix(mix(hash21(i), hash21(i + vec2(1., 0.)), f.x), mix(hash21(i + vec2(0., 1.)), hash21(i + vec2(1., 1.)), f.x), f.y); }',
    'float fbm(vec2 p){ float a = .5, s = 0.; mat2 m = mat2(.8, .6, -.6, .8) * 2.02;',
    '  for (int i = 0; i < 5; i++){ s += a * vnoise(p); p = m * p; a *= .5; } return s * 1.03; }',
    'vec3 pal(float t){ t = clamp(t, 0., 1.) * 3.; return t < 1. ? mix(u_c1, u_c2, t) : (t < 2. ? mix(u_c2, u_c3, t - 1.) : mix(u_c3, u_c4, t - 2.)); }',
    'vec2 pc(){ return (gl_FragCoord.xy * 2. - u_res) / min(u_res.x, u_res.y); }',
    ''
  ].join('\n');

  window.PortfolioShaders = {
    PRE: PRE,
    plasma: {
      colors: ['#1a0910', '#7a1f3d', '#e0674f', '#ffd9a6'],
      frag: [
        'void main(){',
        '  vec2 p = pc() * 1.4; float t = u_time * .22;',
        '  for (int i = 1; i < 6; i++){ float fi = float(i);',
        '    p += vec2(.62 / fi * sin(fi * p.y * 1.15 + t + .3 * fi), .62 / fi * cos(fi * p.x * 1.15 + t * 1.13 + .5 * fi)); }',
        '  float fold = p.x * 1.3 + p.y * .9;',
        '  float sheen = pow(.5 + .5 * sin(fold * 2.2), 3.5);',
        '  float body = .5 + .5 * sin(fold * 1.1 + 1.);',
        '  vec3 col = pal(body * .62 + sheen * .45);',
        '  col *= .55 + .65 * (.5 + .5 * cos(fold * 2.2 - 1.2));',
        '  col += u_c4 * sheen * .22;',
        '  gl_FragColor = vec4(clamp(col, 0., 1.), 1.);',
        '}'
      ].join('\n')
    },
    marble: {
      colors: ['#efe8da', '#c7c0b0', '#1c3a33', '#c9a24b'],
      frag: [
        'void main(){',
        '  vec2 p = pc() * .9; float t = u_time * .05;',
        '  vec2 q = vec2(fbm(p * 1.1 + t), fbm(p * 1.1 + vec2(4.7, 1.3) - t));',
        '  vec2 r = vec2(fbm(p + 2.4 * q + vec2(1.7, 9.2)), fbm(p + 2.4 * q + vec2(8.3, 2.8) + t));',
        '  float f = fbm(p + 2.8 * r);',
        '  float cloud = smoothstep(.25, .85, fbm(p * 2.2 + 3. * q));',
        '  vec3 col = mix(u_c1, u_c2, cloud * .75);',
        '  float vein = pow(1. - abs(sin((p.x * .9 + p.y * .6 + 1.7 * f + .6 * r.x) * 3.1416)), 9.);',
        '  float vein2 = pow(1. - abs(sin((p.x * .5 - p.y * .8 + 2.2 * r.y) * 3.1416 * 1.3)), 40.);',
        '  col = mix(col, u_c3, vein * .92 * (.35 + .65 * cloud));',
        '  col = mix(col, u_c4, vein2 * .85);',
        '  gl_FragColor = vec4(clamp(col, 0., 1.), 1.);',
        '}'
      ].join('\n')
    },
    ink: {
      colors: ['#f1e8d8', '#c9513a', '#2c5557', '#0f1113'],
      frag: [
        'void main(){',
        '  vec2 p = pc() * .85; float t = u_time * .1;',
        '  vec2 q = vec2(fbm(p + t), fbm(p + vec2(5.2, 1.3) - t));',
        '  vec2 r = vec2(fbm(p + 2.6 * q + vec2(1.7, 9.2) + .6 * t), fbm(p + 2.6 * q + vec2(8.3, 2.8) - .5 * t));',
        '  float f = fbm(p + 2.6 * r);',
        '  float k = smoothstep(.2, .85, f * f * 2.1 + .12 * length(q));',
        '  vec3 col = pal(k);',
        '  col = mix(col, u_c4, smoothstep(.55, 1.15, dot(r, r) * 1.5 + f * .6) * smoothstep(.45, .95, k) * .85);',
        '  col += (u_c1 - col) * .12 * smoothstep(.0, .3, f);',
        '  gl_FragColor = vec4(clamp(col, 0., 1.), 1.);',
        '}'
      ].join('\n')
    },
    nebula: {
      colors: ['#04060b', '#0e4a52', '#c2492f', '#ffe3b0'],
      frag: [
        'void main(){',
        '  vec2 p = pc(); float t = u_time;',
        '  vec2 q = vec2(fbm(p * 1.1 + t * .02), fbm(p * 1.1 + 3.7 - t * .015));',
        '  float n = fbm(p * 1.4 + 2.4 * q + vec2(t * .015, 0.));',
        '  float m = fbm(p * 2.1 - 1.8 * q + 11. + t * .01);',
        '  vec3 col = u_c1;',
        '  col = mix(col, u_c2, smoothstep(.3, .75, n) * .95);',
        '  col = mix(col, u_c3, smoothstep(.5, .9, m) * smoothstep(.4, .7, n) * .85);',
        '  col += u_c4 * pow(smoothstep(.62, .95, n * m * 1.6), 2.) * .55;',
        '  for (int l = 0; l < 3; l++){ float fl = float(l); float s = 9. + fl * 10.;',
        '    vec2 g = p * s + vec2(t * (.12 + fl * .07), 0.) + fl * 17.3; vec2 id = floor(g), f = fract(g) - .5;',
        '    float h = hash21(id + fl); vec2 o = (hash22(id) - .5) * .55; float d = length(f - o);',
        '    float tw = .65 + .35 * sin(t * 2.4 + h * 60.);',
        '    float b = step(.84 - fl * .02, h) * smoothstep(.2 - fl * .04, 0., d) * tw;',
        '    col += mix(vec3(.85, .92, 1.), u_c4, hash21(id + 4.)) * b * (1.1 - fl * .25); }',
        '  gl_FragColor = vec4(clamp(col, 0., 1.), 1.);',
        '}'
      ].join('\n')
    }
  };
})();

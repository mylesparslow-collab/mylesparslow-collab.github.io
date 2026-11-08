/* Mockup H "Orbit": fitted type, compare sliders, Esc to Home, and the orbit system (canvas 2D). */
(function () {
  'use strict';
  var D = document, B = D.body, W = window;
  var RM = W.matchMedia && W.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ROOMS = ['legal', 'business', 'creative', 'design', 'research'];
  var COL = { legal: [122, 162, 255], business: [95, 215, 166], creative: [255, 138, 91], design: [255, 209, 102], research: [199, 146, 255] };
  var LET = { legal: 'Legal', business: 'Business', creative: 'Creative', design: 'Design', research: 'Research' };

  /* ---------- fitted type: one line, never wraps, never overflows */
  function fit(el) {
    var s = el.firstElementChild;
    if (!s || s.tagName !== 'SPAN') { s = D.createElement('span'); while (el.firstChild) s.appendChild(el.firstChild); el.appendChild(s); }
    el.style.fontSize = '';
    var w = el.clientWidth; if (!w) return;
    var base = parseFloat(getComputedStyle(el).fontSize), cur = base;
    var max = +el.getAttribute('data-max') || base, min = +el.getAttribute('data-min') || 10, fill = el.getAttribute('data-fit') === 'fill';
    for (var i = 0; i < 4; i++) {
      var sw = s.getBoundingClientRect().width; if (!sw) return;
      var nx = cur * (w - 2) / sw;
      if (!fill) nx = Math.min(nx, base);
      nx = Math.max(min, Math.min(fill ? max : base, nx));
      if (Math.abs(nx - cur) < 0.25 && sw <= w) break;
      cur = Math.floor(nx * 4) / 4; el.style.fontSize = cur + 'px';
    }
  }
  var fits = [];
  function fitAll() { fits = D.querySelectorAll('[data-fit]'); for (var i = 0; i < fits.length; i++) fit(fits[i]); }
  Array.prototype.forEach.call(D.querySelectorAll('.cbody .stats dd'), function (d) { d.setAttribute('data-fit', 'shrink'); d.setAttribute('data-min', '14'); });
  fitAll();
  if (D.fonts && D.fonts.ready) D.fonts.ready.then(fitAll);
  var rz = 0; W.addEventListener('resize', function () { cancelAnimationFrame(rz); rz = requestAnimationFrame(fitAll); });

  /* ---------- before / after sliders */
  Array.prototype.forEach.call(D.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input'); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* ---------- copy email */
  Array.prototype.forEach.call(D.querySelectorAll('.copy'), function (b) {
    b.addEventListener('click', function () {
      var v = b.getAttribute('data-copy');
      var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(v).then(done, function () {});
    });
  });

  /* ---------- Esc on room pages returns Home */
  if (B.getAttribute('data-home')) D.addEventListener('keydown', function (e) {
    var t = e.target;
    if (e.key === 'Escape' && !(t.closest && t.closest('input,textarea,select,video'))) location.href = B.getAttribute('data-home');
  });

  /* ---------- land mask */
  var MW = 144, MH = 60, GRID = (function () {
    var s = atob('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+B/4AAAAAAAAAAAAAAAAAADvj//+AD0AAAAcAAAAAAAABiL8P//8AAAAAMAD4AAAAAAADxLaAP/8AAAACAP/7YIAAAOAAHm/4P/wAAHAAG/////8Aw///9/5cH+AAA/8f+///////If////58HwHAD73////////+A////+BgDgAAPn////////64AEB//+B+AAACLn///////4CAAQAf//x/AAACHP///////gOAAAAH//5/wAALv////////4IAAAAH///6QAAA/////////0AAAAAD///+AAAB//X3/////gAAAAAD///wAAAF6+Dv/////EAAAAAD///AAAAPEu/3////cIAAAAAB//+AAAAPBB/z////kQAAAAAA//+AAAAH8AP/////BgAAAAAAX/4AAAAP/Ov/////iAAAAAAAP8EAAAAf///v////gAAAAAAAH4EAAAA///36////AAAAAAAAA4MAAAB///7/D/f8AAAAAAAAA4gQAAB///7+B8fAAAAAAAAAAPgAAAB///94B4PggAAAAAAAAA4AAAB////gAwHwQAAAAAAAAAI/AAA////wAwEgQAAAAAAAAAB/gAAf///wAIAAIAAAAAAAAAB/4AAAP//gAAKCAAAAAAAAAAD/8AAAD//AAADOAAAAAAAAAAD//AAAD/+AAADOhAAAAAAAAAH//4AAB/8AAABAA8AAAAAAAAD//8AAB/8AAAAYAeAAAAAAAAB//4AAB/8AAAAAAAAAAAAAAAB//wAAB/8QAAAADAAAAAAAAAAf/wAAB/8wAAAAfsAAAAAAAAAP/wAAB/wwAAAA/+AAAAAAAAAP/gAAA/xgAAAH//AAAAAAAAAP+AAAA/gAAAAD//gAAAAAAAAf8AAAAfgAAAAD//gAAAAAAAAf4AAAAfAAAAAD9/gAAAAAAAAfwAAAAAAAAAADAfAAAAAAAAAfgAAAAAAAAAAAAPAAAAAAAAA+AAAAAAAAAAAAAAACAAAAAAAcAAAAAAAAAAAAACAIAAAAAAA4AAAAAAAAAAAAAAAQAAAAAAA4AAAAAAAAEAAAAAAAAAAAAAAwAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAfAH///8AAAAAAAAAeAAAAN7//5/////+AAAAFAbyfAAA////////////wAAf////wAAf///////////+AAQ////+ADg////////////+AAB//////P//////////////A//f/////////////////////////////////////////////'), g = new Uint8Array(MW * MH);
    for (var i = 0; i < MW * MH; i++) g[i] = (s.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1;
    return g;
  })();
  function land(lon, lat) {
    var fx = ((((lon + 180) / 2.5) % MW) + MW) % MW - 0.5, fy = (90 - lat) / 3 - 0.5;
    var x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0;
    function g(x, y) { y = y < 0 ? 0 : y > MH - 1 ? MH - 1 : y; return GRID[y * MW + (((x % MW) + MW) % MW)]; }
    return (g(x0, y0) * (1 - tx) + g(x0 + 1, y0) * tx) * (1 - ty) + (g(x0, y0 + 1) * (1 - tx) + g(x0 + 1, y0 + 1) * tx) * ty;
  }

  /* ---------- 3x3 helpers (row-major) */
  function mul(a, b) {
    var o = new Array(9);
    for (var r = 0; r < 3; r++) for (var c = 0; c < 3; c++) o[r * 3 + c] = a[r * 3] * b[c] + a[r * 3 + 1] * b[3 + c] + a[r * 3 + 2] * b[6 + c];
    return o;
  }
  function view(yaw, pitch) {
    var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    return [cy, 0, sy, sp * sy, cp, -sp * cy, -cp * sy, sp, cp * cy];
  }
  function rotY(a) { var c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 1, 0, -s, 0, c]; }
  function rotZ(a) { var c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; }
  function wrapPi(a) { a = (a + Math.PI) % (2 * Math.PI); if (a < 0) a += 2 * Math.PI; return a - Math.PI; }

  /* five orbits: radius (globe radii), inclination, ascending node, phase */
  var RINGS = [
    { room: 'legal', r: 1.24, inc: -0.66, node: 0.50, ph: 0.2 },
    { room: 'business', r: 1.35, inc: 0.53, node: 2.05, ph: 1.4 },
    { room: 'creative', r: 1.46, inc: 0.85, node: 5.76, ph: 2.6 },
    { room: 'design', r: 1.57, inc: 1.01, node: 1.71, ph: 0.9 },
    { room: 'research', r: 1.68, inc: 0.46, node: 5.21, ph: 3.7 }
  ];
  var RMAX = 1.68;
  RINGS.forEach(function (g) {
    var ci = Math.cos(g.inc), si = Math.sin(g.inc), cn = Math.cos(g.node), sn = Math.sin(g.node);
    g.u = [cn, 0, -sn]; g.v = [ci * sn, -si, ci * cn]; g.n = [si * sn, ci, si * cn];
    g.w = 0.045 * Math.pow(1.24 / g.r, 1.5);
    g.c = COL[g.room]; g.sats = [];
  });
  var RBY = {}; RINGS.forEach(function (g) { RBY[g.room] = g; });

  function Orbit(stage, opt) {
    var sky = stage.querySelector('.sky') || stage, cv = stage.querySelector('canvas'), ctx = cv.getContext('2d');
    var mini = !!opt.mini, only = opt.only || null;
    var lowTier = Math.min(screen.width, screen.height) < 700 || (navigator.hardwareConcurrency || 8) <= 4;
    var DPR = Math.min(W.devicePixelRatio || 1, lowTier ? 1.5 : 2);
    var NF = mini ? 5000 : (lowTier ? 9000 : 18000);
    /* globe points: x,y,z,type (0 ocean,1 land,2 coast,3 graticule) */
    var pts = [], i, ga = Math.PI * (3 - Math.sqrt(5));
    for (i = 0; i < NF; i++) {
      var y = 1 - 2 * (i + 0.5) / NF, rr = Math.sqrt(1 - y * y), ph = i * ga;
      var x = Math.cos(ph) * rr, z = Math.sin(ph) * rr;
      var L = land(Math.atan2(x, z) * 180 / Math.PI, Math.asin(y) * 180 / Math.PI);
      if (L >= 0.5) pts.push(x, y, z, L < 0.86 ? 2 : 1);
      else if (((Math.imul(i, 2654435761) >>> 0) % 997) < 250) pts.push(x, y, z, 0);
    }
    if (!mini) {
      for (var la = -60; la <= 60; la += 30) for (var lo = 0; lo < 360; lo += 2.4) {
        var a1 = la * Math.PI / 180, b1 = lo * Math.PI / 180;
        pts.push(Math.cos(a1) * Math.sin(b1), Math.sin(a1), Math.cos(a1) * Math.cos(b1), 3);
      }
    }
    var P = new Float32Array(pts), NP = P.length / 4;
    var LB = 9, buckets = [], bc = new Int32Array(4 * LB);
    for (i = 0; i < 4 * LB; i++) buckets.push(new Float32Array(NP * 2));
    var TA = [0.42, 1.0, 1.0, 0.24], TS = [1.1, 1.8, 2.1, 1.0];

    var Wd = 0, Ht = 0, R = 0, R0 = 0, cx = 0, cy = 0, cxT = 0, RT = 0, wide = false, PW = 0;
    var yaw = mini ? 0.6 : -0.5, pitch = 0.34, P0 = 0.34, vYaw = 0, target = null;
    var spin = 0.9, t = 0, focus = only, hl = null, hover = null;
    var rim = null, disc = null, spR = 1;
    var labels = {}, labW = {}, labPos = {};
    var tip = stage.querySelector('.tip'), panel = stage.querySelector('.opanel');
    var sats = [];
    (opt.sats || []).forEach(function (s) {
      var g = RBY[s.room]; if (!g) return; g.sats.push(s); s.g = g; sats.push(s);
    });
    RINGS.forEach(function (g) { g.sats.forEach(function (s, k) { s.th = g.ph + 2 * Math.PI * k / g.sats.length; s.sx = -99; s.sy = -99; s.vis = false; }); });
    if (!mini) Array.prototype.forEach.call(stage.querySelectorAll('.olab'), function (b) { labels[b.getAttribute('data-room')] = b; });

    function sprites() {
      var R = R0; spR = R; var s = Math.ceil(R * 1.36 * 2 * DPR) + 2, c = s / 2;
      rim = D.createElement('canvas'); rim.width = rim.height = s;
      var x = rim.getContext('2d'), g = x.createRadialGradient(c, c, R * 0.92 * DPR, c, c, R * 1.34 * DPR);
      g.addColorStop(0, 'rgba(120,150,255,0)'); g.addColorStop(0.17, 'rgba(140,168,255,0.20)'); g.addColorStop(0.32, 'rgba(110,140,240,0.08)'); g.addColorStop(1, 'rgba(90,120,230,0)');
      x.fillStyle = g; x.fillRect(0, 0, s, s);
      disc = D.createElement('canvas'); disc.width = disc.height = s; x = disc.getContext('2d');
      g = x.createRadialGradient(c - R * 0.38 * DPR, c - R * 0.42 * DPR, R * 0.1 * DPR, c, c, R * DPR);
      g.addColorStop(0, '#111c40'); g.addColorStop(0.7, '#0a1230'); g.addColorStop(1, '#070c20');
      x.fillStyle = g; x.beginPath(); x.arc(c, c, R * DPR, 0, Math.PI * 2); x.fill();
      x.strokeStyle = 'rgba(200,214,255,0.16)'; x.lineWidth = DPR; x.beginPath(); x.arc(c, c, R * DPR - DPR * 0.5, 0, Math.PI * 2); x.stroke();
    }
    function layout() {
      var b = sky.getBoundingClientRect();
      Wd = b.width; Ht = b.height; if (!Wd || !Ht) return;
      cv.width = Math.round(Wd * DPR); cv.height = Math.round(Ht * DPR);
      wide = !mini && Wd >= 560; stage.classList.toggle('is-wide', wide);
      R0 = Math.min(Wd, Ht) / (2 * RMAX + (mini ? 0.12 : 0.34));
      PW = Math.min(310, Math.round(Wd * 0.38)); stage.style.setProperty('--pw', PW + 'px');
      for (var k in labels) labW[k] = [labels[k].offsetWidth, labels[k].offsetHeight];
      aim(true);
      R = RT; cx = cxT; cy = Ht / 2 - (mini ? 0 : 8);
      sprites(); dirty = true;
    }
    function aim(snap) {
      if (focus && wide && !mini) {
        var g = RBY[focus];
        RT = Math.min(R0, (Wd - PW - 24) / (g.r + 1), (Ht / 2 - 36) / g.r);
        cxT = Wd - 8 - g.r * RT;
      } else { RT = R0; cxT = Wd / 2; }
      if (snap || RM) { R = RT; cx = cxT; }
    }
    /* orient so ring g faces the viewer, tipped back by 0.5 rad */
    function faceRing(g) {
      var best = null;
      [1, -1].forEach(function (sg) {
        var nx = g.n[0] * sg, ny = g.n[1] * sg, nz = g.n[2] * sg;
        var yw = Math.atan2(-nx, nz), h = Math.sqrt(nx * nx + nz * nz), phi = Math.atan2(ny, h), pt = phi - 0.5;
        if (Math.abs(pt) > 1.35) return;
        var c = { yaw: yaw + wrapPi(yw - yaw), pitch: pt };
        var cost = Math.abs(c.yaw - yaw) + Math.abs(pt - P0) * 1.5;
        if (!best || cost < best.cost) { c.cost = cost; best = c; }
      });
      return best;
    }
    function setFocus(room) {
      if (mini) return;
      focus = room || null; vYaw = 0;
      if (focus) { target = faceRing(RBY[focus]); } else { target = { yaw: yaw, pitch: P0 }; }
      for (var k in labels) labels[k].setAttribute('aria-expanded', k === focus ? 'true' : 'false');
      stage.classList.toggle('is-focus', !!focus);
      if (panel) {
        if (focus) {
          var g = RBY[focus], c = 'rgb(' + g.c.join(',') + ')';
          panel.style.setProperty('--c', c);
          panel.querySelector('.opanel__m').textContent = 'Orbit ' + (ROOMS.indexOf(focus) + 1) + ' of 5 · ' + g.sats.length + ' satellites';
          var src = D.getElementById('lh-' + focus);
          panel.querySelector('.opanel__t').textContent = src ? src.textContent : LET[focus];
          var ol = panel.querySelector('.opanel__l'); ol.innerHTML = '';
          var log = D.querySelector('#log-' + focus + ' .lg__l');
          if (log) Array.prototype.forEach.call(log.children, function (li) { var n = li.cloneNode(true); n.querySelector('a').classList.remove('is-hl'); ol.appendChild(n); });
          panel.querySelector('.opanel__go').setAttribute('href', focus + '/index.html');
          panel.hidden = false;
        } else panel.hidden = true;
      }
      aim(false); if (RM && target) { yaw = target.yaw; pitch = target.pitch; target = null; }
      dirty = true; kick();
    }
    this.setFocus = setFocus;
    this.focus = function () { return focus; };
    this.highlight = function (id) { hl = id; dirty = true; kick(); };
    function bucketPush(ty, a, x, y) {
      var b = (a * LB) | 0; if (b >= LB) b = LB - 1; if (b < 1) return;
      var k = ty * LB + b, n = bc[k]; buckets[k][n] = x; buckets[k][n + 1] = y; bc[k] = n + 2;
    }
    function ringPath(g, V, front, alpha, lw, dash) {
      var N = 220, open = false, apex = null;
      ctx.beginPath();
      for (var j = 0; j <= N; j++) {
        var th = j / N * Math.PI * 2, c = Math.cos(th), s = Math.sin(th);
        var wx = g.r * (g.u[0] * c + g.v[0] * s), wy = g.r * (g.u[1] * c + g.v[1] * s), wz = g.r * (g.u[2] * c + g.v[2] * s);
        var X = V[0] * wx + V[1] * wy + V[2] * wz, Y = V[3] * wx + V[4] * wy + V[5] * wz, Z = V[6] * wx + V[7] * wy + V[8] * wz;
        var sx = (cx + X * R) * DPR, sy = (cy - Y * R) * DPR;
        if (!apex || Y > apex[2]) apex = [cx + X * R, cy - Y * R, Y];
        if ((Z >= 0) === front) { if (open) ctx.lineTo(sx, sy); else { ctx.moveTo(sx, sy); open = true; } }
        else open = false;
      }
      ctx.strokeStyle = 'rgba(' + g.c.join(',') + ',' + alpha + ')'; ctx.lineWidth = lw * DPR;
      ctx.setLineDash(dash ? [2 * DPR, 4 * DPR] : []); ctx.stroke();
      return apex;
    }
    function satPos(s, V) {
      var g = s.g, c = Math.cos(s.th), sn = Math.sin(s.th);
      var wx = g.r * (g.u[0] * c + g.v[0] * sn), wy = g.r * (g.u[1] * c + g.v[1] * sn), wz = g.r * (g.u[2] * c + g.v[2] * sn);
      var X = V[0] * wx + V[1] * wy + V[2] * wz, Y = V[3] * wx + V[4] * wy + V[5] * wz, Z = V[6] * wx + V[7] * wy + V[8] * wz;
      s.sx = cx + X * R; s.sy = cy - Y * R; s.z = Z;
      var dx = X, dy = Y; s.vis = Z >= 0 || dx * dx + dy * dy > 1;
    }
    function ringAlpha(g, front) {
      if (mini) return g.room === only ? (front ? 0.95 : 0.55) : (front ? 0.13 : 0.07);
      if (focus) return g.room === focus ? (front ? 0.95 : 0.6) : (front ? 0.12 : 0.06);
      return front ? 0.62 : 0.3;
    }
    function drawSats(V, front) {
      for (var k = 0; k < sats.length; k++) {
        var s = sats[k]; if ((s.z >= 0) !== front) continue;
        var g = s.g, dimmed = (focus && g.room !== focus) || (mini && g.room !== only);
        var a = (front ? 1 : 0.5) * (dimmed ? 0.22 : 1), r = mini ? 1.8 : 2.6;
        ctx.fillStyle = 'rgba(' + g.c.join(',') + ',' + a + ')';
        ctx.beginPath(); ctx.arc(s.sx * DPR, s.sy * DPR, r * DPR, 0, 6.2832); ctx.fill();
        if (!mini && front && !dimmed) {
          ctx.strokeStyle = 'rgba(' + g.c.join(',') + ',0.35)'; ctx.lineWidth = DPR;
          ctx.beginPath(); ctx.arc(s.sx * DPR, s.sy * DPR, 5.5 * DPR, 0, 6.2832); ctx.stroke();
        }
      }
    }
    function draw() {
      var V = view(yaw, pitch), G = mul(V, mul(rotZ(0.41), rotY(spin)));
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
      for (var k = 0; k < sats.length; k++) satPos(sats[k], V);
      /* back half */
      for (k = 0; k < RINGS.length; k++) ringPath(RINGS[k], V, false, ringAlpha(RINGS[k], false), 1, true);
      drawSats(V, false);
      /* globe */
      var sz = Math.max(0.75, Math.min(1.35, R / 210));
      var sd = rim.width * R / spR, sx0 = cx * DPR - sd / 2, sy0 = cy * DPR - sd / 2;
      ctx.drawImage(rim, sx0, sy0, sd, sd); ctx.drawImage(disc, sx0, sy0, sd, sd);
      bc.fill(0);
      var g0 = G[0], g1 = G[1], g2 = G[2], g3 = G[3], g4 = G[4], g5 = G[5], g6 = G[6], g7 = G[7], g8 = G[8];
      var lx = -0.42, ly = 0.52, lz = 0.74, RD = R * DPR, CX = cx * DPR, CY = cy * DPR;
      for (var j = 0, o = 0; j < NP; j++, o += 4) {
        var x = P[o], y = P[o + 1], z = P[o + 2];
        var Z = g6 * x + g7 * y + g8 * z; if (Z <= 0.02) continue;
        var X = g0 * x + g1 * y + g2 * z, Y = g3 * x + g4 * y + g5 * z, ty = P[o + 3];
        var d = X * lx + Y * ly + Z * lz, sh = 0.3 + 0.7 * (d > 0 ? d : 0);
        var a = TA[ty] * sh * (0.3 + 0.7 * Math.sqrt(Z)) * 1.12;
        bucketPush(ty, a, CX + X * RD, CY - Y * RD);
      }
      ctx.fillStyle = '#dfe6f2';
      for (var ty2 = 0; ty2 < 4; ty2++) {
        var s = TS[ty2] * sz * DPR, h = s / 2;
        for (var b = 1; b < LB; b++) {
          var kk = ty2 * LB + b, n = bc[kk]; if (!n) continue;
          var arr = buckets[kk];
          ctx.globalAlpha = (b + 0.5) / LB; ctx.beginPath();
          if (ty2 === 1 || ty2 === 2) for (var q = 0; q < n; q += 2) { ctx.moveTo(arr[q] + h, arr[q + 1]); ctx.arc(arr[q], arr[q + 1], h, 0, 6.2832); }
          else for (q = 0; q < n; q += 2) ctx.rect(arr[q] - h, arr[q + 1] - h, s, s);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
      /* front half */
      var apex = {};
      for (k = 0; k < RINGS.length; k++) {
        var gg = RINGS[k], on = (focus && gg.room === focus) || (mini && gg.room === only);
        apex[gg.room] = ringPath(gg, V, true, ringAlpha(gg, true), on ? 1.5 : 1.1, false);
      }
      drawSats(V, true);
      /* highlight */
      var hs = hover || findSat(hl);
      if (hs && !mini) {
        var c = 'rgb(' + hs.g.c.join(',') + ')';
        ctx.strokeStyle = c; ctx.lineWidth = 1.5 * DPR; ctx.globalAlpha = hs.vis ? 1 : 0.6;
        ctx.beginPath(); ctx.arc(hs.sx * DPR, hs.sy * DPR, 10 * DPR, 0, 6.2832); ctx.stroke();
        ctx.fillStyle = c; ctx.beginPath(); ctx.arc(hs.sx * DPR, hs.sy * DPR, 3.6 * DPR, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
      }
      if (!mini) { placeLabels(apex); placeTip(hs); }
    }
    function findSat(id) { if (!id) return null; for (var k = 0; k < sats.length; k++) if (sats[k].id === id) return sats[k]; return null; }
    function placeLabels(apex) {
      var L = [], left = (focus && wide) ? PW + 30 : 6;
      for (var k in labels) {
        var a = apex[k], w = labW[k][0], h = labW[k][1];
        L.push({ k: k, x: a[0] - w / 2, y: a[1] - h - 10, w: w, h: h });
      }
      function clampL(p) { p.x = Math.max(left, Math.min(Wd - p.w - 6, p.x)); p.y = Math.max(4, Math.min(Ht - p.h - 28, p.y)); }
      function hit(p, placed) { for (var m = 0; m < placed.length; m++) { var q = placed[m]; if (p.x < q.x + q.w + 6 && q.x < p.x + p.w + 6 && p.y < q.y + q.h + 4 && q.y < p.y + p.h + 4) return true; } return false; }
      L.sort(function (p, q) { return (q.k === focus) - (p.k === focus) || p.y - q.y; });
      var placed = [];
      L.forEach(function (p) {
        var x0 = p.x, y0 = p.y, dy = p.h + 6, dx = p.w * 0.6 + 8, ok = false;
        var C = [[0, 0], [0, -dy], [0, dy], [dx, 0], [-dx, 0], [dx, -dy], [-dx, -dy], [dx, dy], [-dx, dy], [0, -2 * dy], [0, 2 * dy], [2 * dx, 0], [-2 * dx, 0], [0, -3 * dy], [0, 3 * dy]];
        for (var c = 0; c < C.length; c++) { p.x = x0 + C[c][0]; p.y = y0 + C[c][1]; clampL(p); if (!hit(p, placed)) { ok = true; break; } }
        if (!ok) { p.x = x0; p.y = y0; clampL(p); }
        placed.push(p);
      });
      L.forEach(function (p) {
        var o = labPos[p.k];
        if (!o || RM || jump) o = labPos[p.k] = { x: p.x, y: p.y };
        else if (Math.abs(p.x - o.x) + Math.abs(p.y - o.y) > 40) { o.x = p.x; o.y = p.y; }
        else { o.x += (p.x - o.x) * 0.5; o.y += (p.y - o.y) * 0.5; }
        labels[p.k].style.transform = 'translate(' + o.x.toFixed(1) + 'px,' + o.y.toFixed(1) + 'px)';
      });
      jump = false;
    }
    var jump = true;
    function placeTip(s) {
      if (!tip) return;
      if (!s) { tip.hidden = true; return; }
      if (tip.getAttribute('data-id') !== s.id) {
        tip.setAttribute('data-id', s.id);
        tip.querySelector('b').textContent = s.title; tip.querySelector('span').textContent = s.sub;
        tip.querySelector('em').textContent = s.code + ' · ' + LET[s.room];
        tip.style.setProperty('--c', 'rgb(' + s.g.c.join(',') + ')');
        tip.hidden = false; tip._w = tip.offsetWidth; tip._h = tip.offsetHeight;
      }
      tip.hidden = false;
      var left = (focus && wide) ? PW + 30 : 4;
      var x = s.sx + 16, y = s.sy - tip._h - 12;
      if (x + tip._w > Wd - 4) x = s.sx - tip._w - 16;
      if (x < left) x = left;
      if (y < 4) y = s.sy + 16;
      tip.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
    }

    /* ---------- loop */
    var raf = 0, last = 0, running = false, visible = true, dirty = true, stats = W.__orbit = W.__orbit || { dts: [], draw: [] };
    function animating() { return !RM || target || Math.abs(vYaw) > 1e-4 || Math.abs(R - RT) > 0.3 || Math.abs(cx - cxT) > 0.3; }
    function frame(now) {
      raf = 0;
      var dt = last ? Math.min(0.05, (now - last) / 1000) : 0.016; last = now;
      if (!mini) { stats.dts.push(dt * 1000); if (stats.dts.length > 600) stats.dts.shift(); }
      if (!RM) {
        t += dt; spin += dt * (mini ? 0.1 : 0.07);
        for (var k = 0; k < sats.length; k++) sats[k].th += dt * sats[k].g.w;
        if (!drag && Math.abs(vYaw) > 1e-4) { yaw += vYaw * dt; vYaw *= Math.exp(-dt * 2.4); }
      }
      if (target) {
        var e = RM ? 1 : 1 - Math.exp(-dt * 3.4);
        yaw += (target.yaw - yaw) * e; pitch += (target.pitch - pitch) * e;
        if (Math.abs(target.yaw - yaw) < 1e-3 && Math.abs(target.pitch - pitch) < 1e-3) { yaw = target.yaw; pitch = target.pitch; target = null; }
      }
      var e2 = RM ? 1 : 1 - Math.exp(-dt * 4);
      R += (RT - R) * e2; cx += (cxT - cx) * e2;
      var t0 = performance.now(); draw(); dirty = false;
      if (!mini) { stats.draw.push(performance.now() - t0); if (stats.draw.length > 600) stats.draw.shift(); }
      if (running && (animating() || dirty)) raf = requestAnimationFrame(frame);
      else last = 0;
    }
    function kick() { if (running && !raf) { raf = requestAnimationFrame(frame); } }
    function setRun() {
      running = visible && !D.hidden;
      if (running) { dirty = true; kick(); } else if (raf) { cancelAnimationFrame(raf); raf = 0; last = 0; }
    }
    D.addEventListener('visibilitychange', setRun);
    if ('IntersectionObserver' in W) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; setRun(); }, { rootMargin: '40px' }).observe(sky);
    if ('ResizeObserver' in W) new ResizeObserver(function () { layout(); jump = true; kick(); }).observe(sky);
    else W.addEventListener('resize', function () { layout(); kick(); });
    layout(); setRun();

    /* ---------- pointer: drag with inertia, hover, click */
    var drag = null;
    if (mini) return;
    function pick(px, py, rad) {
      var best = null, bd = rad * rad;
      for (var k = 0; k < sats.length; k++) {
        var s = sats[k]; if (!s.vis) continue;
        if (focus && s.g.room !== focus) continue;
        var dx = s.sx - px, dy = s.sy - py, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = s; }
      }
      return best;
    }
    function local(e) { var b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; }
    cv.addEventListener('pointerdown', function (e) {
      var p = local(e);
      drag = { x: p[0], y: p[1], lx: p[0], ly: p[1], t: performance.now(), moved: false, id: e.pointerId, type: e.pointerType, v: 0 };
      vYaw = 0;
    });
    cv.addEventListener('pointermove', function (e) {
      var p = local(e);
      if (drag && drag.id === e.pointerId) {
        var dx = p[0] - drag.lx, dy = p[1] - drag.ly, now = performance.now(), dt = Math.max(1, now - drag.t);
        if (!drag.moved && Math.abs(p[0] - drag.x) + Math.abs(p[1] - drag.y) > 5) {
          drag.moved = true; stage.classList.add('is-drag'); target = null;
          try { cv.setPointerCapture(e.pointerId); } catch (_) {}
        }
        if (drag.moved) {
          var k = 2.6 / Math.max(260, R * 2);
          yaw += dx * k; if (drag.type === 'mouse') pitch = Math.max(-1.2, Math.min(1.25, pitch + dy * k));
          drag.v = drag.v * 0.6 + (dx * k / (dt / 1000)) * 0.4;
          hover = null;
        }
        drag.lx = p[0]; drag.ly = p[1]; drag.t = now; dirty = true; kick();
        return;
      }
      if (e.pointerType === 'mouse') {
        var s = pick(p[0], p[1], 14);
        if (s !== hover) { hover = s; stage.classList.toggle('is-hot', !!s); dirty = true; kick(); }
      }
    });
    function end(e) {
      if (!drag || drag.id !== e.pointerId) return;
      var d = drag; drag = null; stage.classList.remove('is-drag');
      if (d.moved) { if (!RM && performance.now() - d.t < 90) vYaw = Math.max(-3, Math.min(3, d.v)); kick(); return; }
      if (e.type === 'pointercancel') return;
      var p = local(e), s = pick(p[0], p[1], d.type === 'mouse' ? 14 : 22);
      if (s) {
        if (d.type !== 'mouse' && hover !== s) { hover = s; dirty = true; kick(); return; }
        location.href = s.href; return;
      }
      hover = null; stage.classList.remove('is-hot');
      if (focus) setFocus(null); else { dirty = true; kick(); }
    }
    cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
    cv.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse' && hover && !drag) { hover = null; stage.classList.remove('is-hot'); dirty = true; kick(); } });
  }

  /* ---------- homepage system */
  var stage = D.getElementById('stage');
  if (stage) {
    var sats = Array.prototype.map.call(D.querySelectorAll('#log a[data-sat]'), function (a) {
      return { id: a.getAttribute('data-sat'), room: a.getAttribute('data-room'), href: a.getAttribute('href'),
        title: a.querySelector('.lt').textContent, sub: a.querySelector('.ls').textContent, code: a.querySelector('.lc').textContent };
    });
    var orb = new Orbit(stage, { sats: sats });
    Array.prototype.forEach.call(stage.querySelectorAll('.olab'), function (b) {
      b.addEventListener('click', function (e) { e.stopPropagation(); var r = b.getAttribute('data-room'); orb.setFocus(orb.focus() === r ? null : r); });
    });
    var panel = D.getElementById('opanel');
    panel.querySelector('.opanel__x').addEventListener('click', function () { var f = orb.focus(); orb.setFocus(null); var l = stage.querySelector('.olab[data-room="' + f + '"]'); if (l) l.focus(); });
    D.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && orb.focus()) { var f = orb.focus(); orb.setFocus(null); var l = stage.querySelector('.olab[data-room="' + f + '"]'); if (l && (panel.contains(D.activeElement) || D.activeElement === l)) l.focus(); }
    });
    D.addEventListener('click', function (e) {
      if (orb.focus() && !stage.contains(e.target)) orb.setFocus(null);
    });
    function hlFrom(e) { var a = e.target.closest && e.target.closest('a[data-sat]'); return a ? a.getAttribute('data-sat') : null; }
    var cur = null;
    function setHL(id) {
      if (id === cur) return; cur = id; orb.highlight(id);
      Array.prototype.forEach.call(D.querySelectorAll('#log a.is-hl'), function (a) { a.classList.remove('is-hl'); });
      if (id) { var a = D.querySelector('#log a[data-sat="' + id + '"]'); if (a) a.classList.add('is-hl'); }
    }
    [D.getElementById('log'), panel].forEach(function (root) {
      root.addEventListener('focusin', function (e) { setHL(hlFrom(e)); });
      root.addEventListener('focusout', function () { setHL(null); });
      root.addEventListener('mouseover', function (e) { var id = hlFrom(e); if (id) setHL(id); });
      root.addEventListener('mouseleave', function () { setHL(null); });
    });
  }

  /* ---------- room page: small globe with only this room's ring lit */
  var mini = D.getElementById('mini');
  if (mini) {
    var room = B.getAttribute('data-room');
    var ms = Array.prototype.map.call(D.querySelectorAll('.chips a[data-sat]'), function (a) { return { id: a.getAttribute('data-sat'), room: room }; });
    new Orbit(mini, { mini: true, only: room, sats: ms });
  }
})();

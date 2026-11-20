/* Type plate: a block of a project's own write-up, justified, where each letter's
   weight is set by the brightness of the project's screenshot underneath it.
   Canvas 2D, real variable-font weights. plate(canvas, img, text, opts) -> Promise */
(function (g) {
  var WCACHE = {};
  function widths(ctx, family, fs, ref) {
    var k = family + '|' + fs + '|' + ref;
    if (WCACHE[k]) return WCACHE[k];
    ctx.font = ref + ' ' + fs + 'px "' + family + '"';
    var m = {};
    return (WCACHE[k] = { get: function (c) { return m[c] || (m[c] = ctx.measureText(c).width); } });
  }
  function lumGrid(img, cols, rows, fit) {
    var c = document.createElement('canvas'); c.width = cols; c.height = rows;
    var x = c.getContext('2d', { willReadFrequently: true });
    x.imageSmoothingQuality = 'high';
    // cover-fit the image into the grid
    var ir = img.naturalWidth / img.naturalHeight, gr = fit;
    var sw = img.naturalWidth, sh = img.naturalHeight, sx = 0, sy = 0;
    if (ir > gr) { sw = sh * gr; sx = (img.naturalWidth - sw) / 2; } else { sh = sw / gr; sy = 0; }
    x.drawImage(img, sx, sy, sw, sh, 0, 0, cols, rows);
    var d = x.getImageData(0, 0, cols, rows).data, out = new Float32Array(cols * rows);
    for (var i = 0; i < cols * rows; i++) out[i] = (0.2126 * d[i * 4] + 0.7152 * d[i * 4 + 1] + 0.0722 * d[i * 4 + 2]) / 255;
    return { data: out, rgb: d, crop: [sx, sy, sw, sh] };
  }
  function plate(canvas, img, text, o) {
    o = o || {};
    var dpr = o.dpr || Math.min(2, g.devicePixelRatio || 1);
    var W = o.width || canvas.clientWidth, H = o.height || canvas.clientHeight;
    var fs = o.size || 12, lh = o.leading || Math.round(fs * 1.32), family = o.family || 'Epilogue';
    var ink = o.ink || '#141412', paper = o.paper || null, dark = !!o.dark;
    var lo = o.lo || 100, hi = o.hi || 900, steps = o.steps || 17, ref = o.ref || 480;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (paper) { ctx.fillStyle = paper; ctx.fillRect(0, 0, W, H); } else ctx.clearRect(0, 0, W, H);
    var wd = widths(ctx, family, fs, ref), space = wd.get(' ');
    var rows = Math.floor(H / lh), cellW = fs * 0.5, cols = Math.ceil(W / cellW);
    var L = lumGrid(img, cols, rows * 2, W / H);
    // stats for auto contrast
    var arr = Array.prototype.slice.call(L.data).sort(function (a, b) { return a - b; });
    var p5 = arr[Math.floor(arr.length * .04)], p95 = arr[Math.floor(arr.length * .96)], span = Math.max(.12, p95 - p5);
    var words = text.split(/\s+/).filter(Boolean), wi = 0, y, buckets = {};
    function put(ch, x, yy) {
      var cx = Math.min(cols - 1, Math.max(0, Math.floor((x + wd.get(ch) / 2) / cellW)));
      var cy = Math.min(rows * 2 - 1, Math.floor((yy / lh) * 2 + 1));
      var l = (L.data[cy * cols + cx] + L.data[Math.max(0, cy - 1) * cols + cx]) / 2;
      var t = Math.min(1, Math.max(0, (l - p5) / span));       // 0 dark .. 1 light
      if (dark) t = 1 - t;                                       // dark theme: light pixels get the heavy letters
      t = Math.pow(t, o.gamma || 1);
      var w = hi - (hi - lo) * t;                                // dark pixel -> heavy letter
      var q = Math.round((w - lo) / (hi - lo) * (steps - 1));
      var col = null;
      if (o.colour) { var ii = (cy * cols + cx) * 4, R = L.rgb[ii], G = L.rgb[ii + 1], B = L.rgb[ii + 2];
        var mx = Math.max(R, G, B, 1), k2 = Math.max(1, (o.floor || 110) / mx);   // lift very dark pixels so letters stay visible
        col = 'rgb(' + Math.min(255, R * k2 | 0) + ',' + Math.min(255, G * k2 | 0) + ',' + Math.min(255, B * k2 | 0) + ')'; }
      (buckets[q] || (buckets[q] = [])).push(ch, x, yy, col);
    }
    for (var r = 0; r < rows; r++) {
      y = r * lh + lh * .78;
      // gather words for this line
      var line = [], lw = 0;
      while (true) {
        var word = words[wi % words.length], ww = 0;
        for (var k = 0; k < word.length; k++) ww += wd.get(word[k]);
        if (line.length && lw + space + ww > W) break;
        lw += (line.length ? space : 0) + ww; line.push([word, ww]); wi++;
        if (lw > W) break;
      }
      var gaps = line.length - 1, extra = gaps > 0 ? (W - lw) / gaps : 0, x = 0;
      for (var a = 0; a < line.length; a++) {
        var s = line[a][0];
        for (var b = 0; b < s.length; b++) { put(s[b], x, y); x += wd.get(s[b]); }
        x += space + extra;
      }
    }
    ctx.fillStyle = ink; ctx.textBaseline = 'alphabetic';
    Object.keys(buckets).forEach(function (q) {
      var w = Math.round(lo + (hi - lo) * q / (steps - 1));
      ctx.font = w + ' ' + fs + 'px "' + family + '"';
      var bk = buckets[q];
      for (var i = 0; i < bk.length; i += 4) { if (bk[i + 3]) ctx.fillStyle = bk[i + 3]; ctx.fillText(bk[i], bk[i + 1], bk[i + 2]); }
    });
    return { rows: rows, lh: lh, crop: L.crop };
  }
  g.typePlate = plate;
})(window);

/* site-kit product template: buy box, gallery, bundles, sticky bar, cart, checkout. No dependencies. */
(function () {
  "use strict";
  var B = document.body, ROOT = B.dataset.root || "", IDX = B.dataset.idx || "", CUR = B.dataset.currency || "USD";
  var KEY = "site-kit-cart:" + (B.dataset.store || "product"), mem = null;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  var fmt;
  try { fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: CUR }); } catch (e) { fmt = { format: function (n) { return CUR + " " + n.toFixed(2); } }; }
  var DATA = {};
  try { DATA = JSON.parse($("#sk-data").textContent) || {}; } catch (e) {}
  var P = DATA.products || {}, MAIN = P[DATA.main];

  function el(tag, props, kids) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      if (k === "text") n.textContent = props[k]; else if (k === "class") n.className = props[k]; else n.setAttribute(k, props[k]);
    });
    (kids || []).forEach(function (c) { n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  var src = function (s) { return /^https?:/.test(s) ? s : ROOT + s; };
  var href = function (path) { return ROOT + path + IDX; };

  /* price for qty items: real bundle prices where they fit, the plain unit price for the rest.
     Greedy: take the biggest bundle that fits, repeat, charge the remainder per item. */
  function total(p, unit, qty) {
    var rem = qty, sum = 0;
    if (unit === p.price) {
      (p.tiers || []).slice().sort(function (a, b) { return b.qty - a.qty; }).forEach(function (t) {
        while (rem >= t.qty) { sum += t.price; rem -= t.qty; }
      });
    }
    return Math.round((sum + rem * unit) * 100) / 100;
  }

  /* cart storage: always inside try/catch, with an in-memory fallback */
  function load() {
    if (mem) return mem;
    try { var a = JSON.parse(localStorage.getItem(KEY) || "[]"); return Array.isArray(a) ? a : []; } catch (e) { return []; }
  }
  function save(items) {
    mem = null;
    try { localStorage.setItem(KEY, JSON.stringify(items)); } catch (e) { mem = items; }
    count();
  }
  function count() {
    var n = load().reduce(function (s, i) { return s + (i.qty || 0); }, 0);
    $$("[data-cart-count]").forEach(function (c) { c.textContent = n; c.hidden = !n; });
  }
  function addToCart(id, variant, n) {
    var items = load(), hit = items.filter(function (i) { return i.id === id && (i.variant || null) === variant; })[0];
    if (hit) hit.qty = Math.min(99, hit.qty + n); else items.push({ id: id, variant: variant, qty: Math.min(99, n) });
    save(items);
  }
  window.addEventListener("storage", function (e) { if (e.key === KEY) { count(); if (B.dataset.page === "cart") cart(); } });

  /* newsletter demo */
  $$("[data-demo-form]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var m = $("[data-demo-msg]"); if (m) m.textContent = "Demo form: nothing was sent.";
    });
  });

  /* video: load the YouTube player (youtube-nocookie) only after a click */
  $$("[data-yt]").forEach(function (box) {
    var a = $("a", box); if (!a) return;
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var f = el("iframe", { src: box.getAttribute("data-yt"), title: "Product video", allow: "autoplay; encrypted-media; picture-in-picture", allowfullscreen: "", referrerpolicy: "strict-origin-when-cross-origin" });
      box.textContent = ""; box.appendChild(f); f.focus();
    });
  });

  /* product page: gallery, choices, bundles, add to cart, buy now, sticky bar */
  function product() {
    var form = $("#buy"); if (!form || !MAIN) return;
    var rec = MAIN, cols = $$("input[name=color]", form), opts = $$("input[name=option]", form), tierIn = $$("input[name=tier]", form);
    var qtyEl = $("#qty"), msg = $("#buy-msg"), addBtn = $("#add"), nowBtn = $("#buy-now");
    var main = $("#g-img"), frame = $(".g-main"), thumbs = $("#thumbs"), shown = null;
    var checked = function (list) { var i = -1; list.forEach(function (r, k) { if (r.checked) i = k; }); return i; };
    var qty = function () { return Math.max(1, Math.min(99, parseInt(qtyEl && qtyEl.value, 10) || 1)); };
    function cur() {
      var c = rec.colors[checked(cols)] || null, o = rec.options[checked(opts)] || null;
      var unit = o && o.price != null ? o.price : (c && c.price != null ? c.price : rec.price);
      return { c: c, o: o, unit: unit, sold: !!((c && c.sold) || (o && o.sold)),
               name: [c && c.name, o && o.name].filter(Boolean).join(" / ") || null };
    }

    /* gallery */
    function show(a) {
      if (!main) return;
      main.src = a.getAttribute("href"); main.alt = a.getAttribute("data-alt") || main.alt;
      $$(".thumb", thumbs).forEach(function (x) { x.removeAttribute("aria-current"); }); a.setAttribute("aria-current", "true");
      var st = $("#s-thumb"); if (st) st.src = main.src;
    }
    function bindThumbs() {
      var list = $$(".thumb", thumbs);
      list.forEach(function (t, i) {
        t.addEventListener("click", function (e) { e.preventDefault(); show(t); });
        t.addEventListener("keydown", function (e) {
          var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : -1;
          if (j >= 0 && j < list.length) { e.preventDefault(); list[j].focus(); show(list[j]); }
        });
      });
      if (list[0]) list[0].setAttribute("aria-current", "true");
    }
    function setGallery(imgs) {
      imgs = imgs.filter(function (i) { return i.src; });
      if (!imgs.length || !frame) return;
      if (!main) { main = el("img", { id: "g-img", src: src(imgs[0].src), alt: imgs[0].alt }); var ph = $("#g-ph"); if (ph) ph.remove(); frame.appendChild(main); }
      main.src = src(imgs[0].src); main.alt = imgs[0].alt;
      var st = $("#s-thumb"); if (st) st.src = main.src;
      if (!thumbs) return;
      thumbs.textContent = "";
      imgs.forEach(function (i, n) {
        thumbs.appendChild(el("li", {}, [el("a", { href: src(i.src), class: "thumb", "data-alt": i.alt, "aria-label": "Show photo " + (n + 1) }, [el("img", { src: src(i.src), alt: "", loading: "lazy", decoding: "async" })])]));
      });
      thumbs.hidden = imgs.length < 2;
      bindThumbs();
    }
    if (thumbs) bindThumbs();

    /* everything that depends on the choices */
    function render(colorChanged) {
      var s = cur(), n = qty(), t = total(rec, s.unit, n);
      var priceEl = $("#p-price"), cmp = $("#p-compare"), note = $("#p-note"), cn = $("#c-name"), tiers = $("#tiers");
      if (priceEl) priceEl.textContent = fmt.format(t);
      if (cmp) { var showCmp = rec.compareAt && rec.compareAt > rec.price && s.unit === rec.price; cmp.hidden = !showCmp; if (showCmp) cmp.textContent = fmt.format(rec.compareAt * n); }
      if (note) note.textContent = n > 1 ? n + " items, " + fmt.format(t / n) + " each" : "";
      if (cn && s.c) cn.textContent = s.c.name;
      if (tiers) tiers.hidden = s.unit !== rec.price;
      tierIn.forEach(function (r) { r.checked = parseInt(r.value, 10) === n && s.unit === rec.price; });
      if (colorChanged && s.c) setGallery(s.c.gallery);
      [addBtn, nowBtn, $("#s-add")].forEach(function (b) { if (b) b.disabled = s.sold; });
      if (addBtn) addBtn.textContent = s.sold ? "Sold out" : "Add to cart";
      var sb = $("#s-add"); if (sb) sb.textContent = s.sold ? "Sold out" : "Add to cart";
      var sub = $("#s-sub"); if (sub) sub.textContent = (s.name ? s.name + " · " : "") + fmt.format(t);
    }
    cols.concat(opts).forEach(function (r) { r.addEventListener("change", function () { render(cols.indexOf(r) >= 0); }); });
    tierIn.forEach(function (r) { r.addEventListener("change", function () { if (qtyEl) qtyEl.value = r.value; render(false); }); });
    if (qtyEl) { qtyEl.addEventListener("input", function () { render(false); }); qtyEl.addEventListener("change", function () { qtyEl.value = qty(); render(false); }); }
    render(false);

    function add(into) {
      var s = cur(), n = qty();
      if (s.sold) return false;
      if ((rec.colors.length || rec.options.length) && (rec.colors.length && !s.c || rec.options.length && !s.o)) { into.textContent = "Please choose an option."; return false; }
      addToCart(rec.id, s.name, n);
      return true;
    }
    function done(into) {
      into.textContent = "Added to your cart. ";
      into.appendChild(el("a", { href: href("cart/"), text: "View cart" }));
    }
    form.addEventListener("submit", function (e) { e.preventDefault(); if (add(msg)) done(msg); });
    if (nowBtn) nowBtn.addEventListener("click", function () { if (add(msg)) location.href = href("cart/"); });

    /* final CTA band repeats the buy button with the current choices */
    $$("[data-quick-add]").forEach(function (b) {
      b.addEventListener("click", function (e) {
        e.preventDefault();
        var m = $("[data-quick-msg]"); if (add(m)) done(m);
      });
    });
    /* accessories */
    $$("[data-addon]").forEach(function (b) {
      b.addEventListener("click", function () {
        var m = $("[data-addon-msg=\"" + b.getAttribute("data-addon") + "\"]");
        addToCart(b.getAttribute("data-addon"), null, 1);
        if (m) done(m);
      });
    });

    /* sticky bar: shown once the hero Add to cart button has scrolled above the viewport */
    var bar = $("#sticky"), sadd = $("#s-add");
    if (bar && addBtn) {
      var set = function (on) {
        bar.setAttribute("data-show", on ? "true" : "false"); bar.setAttribute("aria-hidden", on ? "false" : "true");
        if (on) bar.removeAttribute("inert"); else bar.setAttribute("inert", "");
      };
      if (sadd) sadd.addEventListener("click", function () {
        if (!add(msg)) return;
        sadd.textContent = "Added"; setTimeout(function () { render(false); }, 1600);
      });
      if (typeof IntersectionObserver === "function") {
        new IntersectionObserver(function (es) {
          es.forEach(function (x) { set(!x.isIntersecting && x.boundingClientRect.top < 0); });
        }).observe(addBtn);
      } else {
        var check = function () { set(addBtn.getBoundingClientRect().bottom < 0); };
        window.addEventListener("scroll", check, { passive: true }); check();
      }
    }
  }

  /* cart */
  function cart() {
    var root = $("#cart"); if (!root) return;
    var C = DATA.checkout || { mode: "demo" }, stored = load(), lines = [];
    stored.forEach(function (it) {
      var p = P[it.id]; if (!p) return;
      var v = null;
      if (p.variants.length) { v = p.variants.filter(function (x) { return x.name === it.variant; })[0]; if (!v) return; }
      var unit = v ? v.price : p.price;
      lines.push({ it: it, p: p, v: v, unit: unit, sold: v ? v.sold : p.sold, link: (v && v.link) || p.link, image: (v && v.image) || p.image });
    });
    if (lines.length !== stored.length) save(lines.map(function (l) { return l.it; }));
    root.textContent = "";
    if (!lines.length) {
      root.appendChild(el("div", { class: "empty-cart" }, [el("p", { text: "Your cart is empty." }), el("a", { class: "btn primary", href: ROOT + IDX, text: "Back to " + (MAIN ? MAIN.title : "the product") })]));
      return;
    }
    var list = el("ul", { "aria-label": "Items in your cart" }), subtotal = 0, blocked = false;
    lines.forEach(function (l) {
      l.total = total(l.p, l.unit, l.it.qty);
      subtotal += l.sold ? 0 : l.total; blocked = blocked || l.sold;
      var thumb = el("span", { class: "media" });
      if (l.image) thumb.appendChild(el("img", { src: src(l.image), alt: "", loading: "lazy" }));
      var q = el("input", { id: "q-" + l.p.id + "-" + (l.v ? l.v.name : ""), type: "number", min: "1", max: "99", value: l.it.qty, "aria-label": "Quantity for " + l.p.title });
      q.addEventListener("change", function () {
        l.it.qty = Math.max(1, Math.min(99, parseInt(q.value, 10) || 1)); save(stored); cart();
      });
      var rm = el("button", { class: "link", type: "button", text: "Remove" });
      rm.addEventListener("click", function () { stored.splice(stored.indexOf(l.it), 1); save(stored); cart(); });
      var info = el("div", {}, [el("h2", {}, [el("a", { href: ROOT + IDX + (l.p.url || ""), text: l.p.title })])]);
      info.appendChild(el("p", { class: "meta", text: (l.v ? l.v.name + ", " : "") + fmt.format(l.unit) + " each" + (l.total < l.unit * l.it.qty ? ", bundle price applied" : "") }));
      info.appendChild(el("div", { class: "row" }, [q, rm]));
      if (l.sold) info.appendChild(el("p", { class: "gone", text: "This item is sold out. Remove it to continue." }));
      list.appendChild(el("li", { class: "line" }, [thumb, info, el("p", { class: "tot", text: l.sold ? "" : fmt.format(l.total) })]));
    });

    var sum = el("aside", { class: "summary", "aria-labelledby": "sum-h" }, [el("h2", { id: "sum-h", text: "Order summary" }),
      el("p", { class: "sum-row" }, [el("span", { text: "Subtotal" }), el("strong", { text: fmt.format(subtotal) })])]);
    if (C.shippingNote) sum.appendChild(el("p", { class: "fine muted", text: C.shippingNote }));
    var status = el("p", { class: "note", role: "status" });

    if (C.mode === "links") {
      if (lines.length === 1) {
        var only = lines[0];
        if (only.link && !blocked) {
          sum.appendChild(el("a", { class: "btn primary block", href: only.link, rel: "noopener", text: "Checkout" }));
          if (only.it.qty > 1) sum.appendChild(el("p", { class: "fine muted", text: "Choose the quantity again on the payment page." }));
        } else sum.appendChild(el("p", { class: "err", text: blocked ? "Remove sold-out items to continue." : "This item has no payment link yet." + (DATA.email ? " Please email " + DATA.email + "." : "") }));
      } else {
        sum.appendChild(el("p", { class: "fine", text: "Each item is paid for separately. Use the Pay button next to each item. Items stay in your cart until you remove them." }));
        var pl = el("ul", { class: "pay-list" });
        lines.forEach(function (l) {
          var label = l.p.title + (l.v ? " (" + l.v.name + ")" : "");
          pl.appendChild(el("li", {}, [el("span", { text: label + ", " + fmt.format(l.total) }),
            l.link && !l.sold ? el("a", { class: "btn ghost", href: l.link, target: "_blank", rel: "noopener", text: "Pay for this item" })
              : el("span", { class: "err", text: l.sold ? "Sold out" : "No payment link yet" })]));
        });
        sum.appendChild(pl);
      }
    } else {
      var go = el("button", { class: "btn primary block", type: "button", text: C.mode === "demo" ? "Checkout (demo)" : "Checkout" });
      if (blocked) { go.disabled = true; sum.appendChild(go); sum.appendChild(el("p", { class: "err", text: "Remove sold-out items to continue." })); }
      else {
        sum.appendChild(go);
        if (C.mode === "demo") sum.appendChild(el("p", { class: "fine muted", text: "Demo store: nothing is charged." }));
        go.addEventListener("click", function () {
          if (C.mode === "demo") {
            var o = el("div", { class: "order" }, [el("p", {}, [el("strong", { text: "Demo order summary" })])]);
            var ol = el("ul"); lines.forEach(function (l) {
              ol.appendChild(el("li", {}, [el("span", { text: l.it.qty + " x " + l.p.title + (l.v ? " (" + l.v.name + ")" : "") }), el("span", { text: fmt.format(l.total) })]));
            });
            o.appendChild(ol); o.appendChild(el("p", { class: "fine", text: "Subtotal " + fmt.format(subtotal) + ". Demo store: nothing is charged and no order is placed." }));
            var old = $(".order", sum); if (old) old.remove(); sum.appendChild(o); return;
          }
          go.disabled = true; status.className = "note"; status.textContent = "Starting checkout...";
          fetch(C.endpoint, { method: "POST", headers: { "content-type": "application/json" },
            body: JSON.stringify({ items: lines.map(function (l) { return { id: l.p.id, variant: l.v ? l.v.name : null, qty: l.it.qty }; }) }) })
            .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
            .then(function (x) {
              if (x.ok && typeof x.j.url === "string" && /^https:\/\/|^http:\/\/localhost/.test(x.j.url)) { location.href = x.j.url; return; }
              throw new Error(x.j && typeof x.j.error === "string" ? x.j.error : "Checkout is unavailable right now.");
            })
            .catch(function (err) {
              go.disabled = false; status.className = "note err";
              status.textContent = err instanceof TypeError ? "Could not reach checkout. Check your connection and try again." : err.message;
            });
        });
      }
    }
    if (C.note) sum.appendChild(el("p", { class: "fine muted", text: C.note }));
    sum.appendChild(status);
    root.appendChild(el("div", { class: "cart-grid" }, [list, sum]));
  }

  count(); product(); cart();
})();

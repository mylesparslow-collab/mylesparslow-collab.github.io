/* site-kit store template: menu, shop filters, gallery, cart, checkout. No dependencies. */
(function () {
  "use strict";
  var B = document.body, ROOT = B.dataset.root || "", IDX = B.dataset.idx || "", CUR = B.dataset.currency || "USD";
  var KEY = "site-kit-cart:" + (B.dataset.store || "store"), mem = null;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  var fmt;
  try { fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: CUR }); } catch (e) { fmt = { format: function (n) { return CUR + " " + n.toFixed(2); } }; }
  var DATA = {};
  try { DATA = JSON.parse($("#sk-data").textContent) || {}; } catch (e) {}
  var P = DATA.products || {};

  function el(tag, props, kids) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      if (k === "text") n.textContent = props[k]; else if (k === "class") n.className = props[k]; else n.setAttribute(k, props[k]);
    });
    (kids || []).forEach(function (c) { n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  var href = function (path) { return ROOT + path + IDX; };

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
  window.addEventListener("storage", function (e) { if (e.key === KEY) { count(); if (B.dataset.page === "cart") cart(); } });

  /* header menu */
  var mb = $(".menu-btn"), nav = $("#nav");
  if (mb && nav) {
    mb.addEventListener("click", function () {
      var open = nav.hasAttribute("data-open");
      if (open) nav.removeAttribute("data-open"); else nav.setAttribute("data-open", "");
      mb.setAttribute("aria-expanded", String(!open));
    });
  }

  /* newsletter demo */
  $$("[data-demo-form]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var m = $("[data-demo-msg]"); if (m) m.textContent = "Demo form: nothing was sent.";
    });
  });

  /* shop: filter, sort, count */
  function shop() {
    var grid = $("#grid"); if (!grid) return;
    var cards = $$(".card", grid), sels = $$("select[data-filter]"), sort = $("#f-sort");
    var res = $("#result"), clr = $("#clear"), empty = $("#empty"), title = $("[data-shop-title]"), blurb = $("[data-shop-blurb]");
    var base = document.title;
    function readUrl() {
      var q = new URLSearchParams(location.search);
      sels.forEach(function (s) {
        var k = s.dataset.filter === "collection" ? "collection" : s.dataset.filter.replace(/^f-/, "");
        var v = q.get(k); if (v && $$("option", s).some(function (o) { return o.value === v; })) s.value = v;
      });
      if (sort && q.get("sort")) sort.value = q.get("sort");
    }
    function writeUrl() {
      var q = new URLSearchParams();
      sels.forEach(function (s) { if (s.value) q.set(s.dataset.filter === "collection" ? "collection" : s.dataset.filter.replace(/^f-/, ""), s.value); });
      if (sort && sort.value !== "feat") q.set("sort", sort.value);
      try { history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q : "")); } catch (e) {}
    }
    function apply() {
      var mode = sort ? sort.value : "feat", shown = [];
      cards.forEach(function (c) {
        var ok = sels.every(function (s) { return !s.value || c.getAttribute("data-" + s.dataset.filter) === s.value; });
        c.hidden = !ok; if (ok) shown.push(c);
      });
      var num = function (c, k) { return parseFloat(c.getAttribute("data-" + k)) || 0; };
      var by = { feat: function (a, b) { return num(a, "feat") - num(b, "feat"); }, new: function (a, b) { return num(a, "new") - num(b, "new"); },
                 asc: function (a, b) { return num(a, "price") - num(b, "price") || num(a, "feat") - num(b, "feat"); },
                 desc: function (a, b) { return num(b, "price") - num(a, "price") || num(a, "feat") - num(b, "feat"); } };
      cards.slice().sort(by[mode] || by.feat).forEach(function (c) { grid.appendChild(c); });
      if (res) res.textContent = shown.length + (shown.length === 1 ? " product" : " products");
      var active = sels.some(function (s) { return s.value; });
      if (clr) clr.hidden = !active;
      if (empty) empty.hidden = !!shown.length;
      var col = sels.filter(function (s) { return s.dataset.filter === "collection" && s.value; })[0];
      var opt = col && col.options[col.selectedIndex];
      if (title) title.textContent = opt ? opt.textContent : "Shop";
      if (blurb) blurb.textContent = opt ? opt.getAttribute("data-blurb") || "" : "";
      document.title = opt ? opt.textContent + " · " + base.split(" · ").slice(1).join(" · ") : base;
    }
    function reset() { sels.forEach(function (s) { s.value = ""; }); writeUrl(); apply(); }
    sels.concat(sort ? [sort] : []).forEach(function (s) { s.addEventListener("change", function () { writeUrl(); apply(); }); });
    if (clr) clr.addEventListener("click", reset);
    var ec = $("#empty-clear"); if (ec) ec.addEventListener("click", reset);
    readUrl(); apply();
  }

  /* product page: gallery, variants, add to cart */
  function product() {
    var art = $(".pdp"); if (!art) return;
    var rec = P[art.dataset.product]; if (!rec) return;
    var img = $("#g-img"), thumbs = $$(".thumb"), price = $("#p-price"), from = $("[data-from]");
    function show(t) {
      if (!img) return;
      img.src = t.getAttribute("href"); img.alt = t.dataset.alt || img.alt;
      thumbs.forEach(function (x) { x.removeAttribute("aria-current"); }); t.setAttribute("aria-current", "true");
    }
    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function (e) { e.preventDefault(); show(t); });
      t.addEventListener("keydown", function (e) {
        var j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : -1;
        if (j >= 0 && j < thumbs.length) { e.preventDefault(); thumbs[j].focus(); show(thumbs[j]); }
      });
    });
    if (thumbs[0]) thumbs[0].setAttribute("aria-current", "true");
    var radios = $$("input[name=variant]");
    function chosen() { var r = radios.filter(function (x) { return x.checked; })[0]; return r ? r.value : null; }
    function upd() {
      var r = radios.filter(function (x) { return x.checked; })[0];
      if (r && price) { price.textContent = fmt.format(parseFloat(r.dataset.price)); if (from) from.hidden = true; }
    }
    radios.forEach(function (r) { r.addEventListener("change", upd); }); upd();
    var form = $("#buy"), msg = $("#buy-msg"), qty = $("#qty"), add = $("#add");
    if (!form || !add) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var v = chosen(), n = rec.one ? 1 : Math.max(1, Math.min(99, parseInt(qty && qty.value, 10) || 1));
      if (rec.variants.length && v === null) { msg.textContent = "Please choose an option."; return; }
      var items = load(), hit = items.filter(function (i) { return i.id === rec.id && (i.variant || null) === v; })[0];
      if (hit && rec.one) { msg.textContent = "This one is already in your cart."; }
      else {
        if (hit) hit.qty = Math.min(99, hit.qty + n); else items.push({ id: rec.id, variant: v, qty: n });
        save(items);
        msg.textContent = "Added to your cart. ";
        msg.appendChild(el("a", { href: href("cart/"), text: "View cart" }));
      }
    });
  }

  /* cart */
  function cart() {
    var root = $("#cart"); if (!root) return;
    var C = DATA.checkout || { mode: "demo" }, stored = load(), lines = [];
    stored.forEach(function (it) {
      var p = P[it.id]; if (!p) return;
      var v = null;
      if (p.variants.length) { v = p.variants.filter(function (x) { return x.name === it.variant; })[0]; if (!v) return; }
      lines.push({ it: it, p: p, v: v, unit: v ? v.price : p.price, sold: v ? v.sold : p.sold, link: (v && v.link) || p.link });
    });
    if (lines.length !== stored.length) save(lines.map(function (l) { return l.it; }));
    root.textContent = "";
    if (!lines.length) {
      root.appendChild(el("div", { class: "empty-cart" }, [el("p", { text: "Your cart is empty." }), el("a", { class: "btn", href: href("shop/"), text: "Browse the shop" })]));
      return;
    }
    var list = el("ul", { "aria-label": "Items in your cart" }), subtotal = 0, blocked = false;
    lines.forEach(function (l) {
      subtotal += l.sold ? 0 : l.unit * l.it.qty; blocked = blocked || l.sold;
      var thumb = el("span", { class: "media" });
      if (l.p.image) thumb.appendChild(el("img", { src: /^https?:/.test(l.p.image) ? l.p.image : ROOT + l.p.image, alt: "", loading: "lazy" }));
      var q = el("input", { id: "q-" + l.p.id + "-" + (l.v ? l.v.name : ""), type: "number", min: "1", max: l.p.one ? "1" : "99", value: l.it.qty, "aria-label": "Quantity for " + l.p.title });
      if (l.p.one) q.setAttribute("readonly", "");
      q.addEventListener("change", function () {
        l.it.qty = Math.max(1, Math.min(l.p.one ? 1 : 99, parseInt(q.value, 10) || 1)); save(stored); cart();
      });
      var rm = el("button", { class: "link", type: "button", text: "Remove" });
      rm.addEventListener("click", function () { stored.splice(stored.indexOf(l.it), 1); save(stored); cart(); });
      var info = el("div", {}, [el("h2", {}, [el("a", { href: href("p/" + l.p.id + "/"), text: l.p.title })])]);
      info.appendChild(el("p", { class: "meta", text: (l.v ? l.v.name + ", " : "") + fmt.format(l.unit) + (l.p.one ? ", one of a kind" : "") }));
      info.appendChild(el("div", { class: "row" }, [q, rm]));
      if (l.sold) info.appendChild(el("p", { class: "gone", text: "This item is sold out. Remove it to continue." }));
      list.appendChild(el("li", { class: "line" }, [thumb, info, el("p", { class: "tot", text: l.sold ? "" : fmt.format(l.unit * l.it.qty) })]));
    });

    var sum = el("aside", { class: "summary", "aria-labelledby": "sum-h" }, [el("h2", { id: "sum-h", text: "Order summary" }),
      el("p", { class: "sum-row" }, [el("span", { text: "Subtotal" }), el("strong", { text: fmt.format(subtotal) })])]);
    if (C.shippingNote) sum.appendChild(el("p", { class: "fine muted", text: C.shippingNote }));
    var status = el("p", { class: "note", role: "status" });

    if (C.mode === "links") {
      if (lines.length === 1) {
        var only = lines[0];
        if (only.link && !blocked) {
          sum.appendChild(el("a", { class: "btn block", href: only.link, rel: "noopener", text: "Checkout" }));
          if (only.it.qty > 1) sum.appendChild(el("p", { class: "fine muted", text: "Choose the quantity again on the payment page." }));
        } else sum.appendChild(el("p", { class: "err", text: blocked ? "Remove sold-out items to continue." : "This item has no payment link yet." + (DATA.email ? " Please email " + DATA.email + "." : "") }));
      } else {
        sum.appendChild(el("p", { class: "fine", text: "Each item is paid for separately. Use the Pay button next to each item. Items stay in your cart until you remove them." }));
        var pl = el("ul", { class: "pay-list" });
        lines.forEach(function (l) {
          var label = l.p.title + (l.v ? " (" + l.v.name + ")" : "");
          pl.appendChild(el("li", {}, [el("span", { text: label + ", " + fmt.format(l.unit * l.it.qty) }),
            l.link && !l.sold ? el("a", { class: "btn ghost", href: l.link, target: "_blank", rel: "noopener", text: "Pay for this item" })
              : el("span", { class: "err", text: l.sold ? "Sold out" : "No payment link yet" })]));
        });
        sum.appendChild(pl);
      }
    } else {
      var go = el("button", { class: "btn block", type: "button", text: C.mode === "demo" ? "Checkout (demo)" : "Checkout" });
      if (blocked) { go.disabled = true; sum.appendChild(go); sum.appendChild(el("p", { class: "err", text: "Remove sold-out items to continue." })); }
      else {
        sum.appendChild(go);
        if (C.mode === "demo") sum.appendChild(el("p", { class: "fine muted", text: "Demo store: nothing is charged." }));
        go.addEventListener("click", function () {
          if (C.mode === "demo") {
            var o = el("div", { class: "order" }, [el("p", {}, [el("strong", { text: "Demo order summary" })])]);
            var ol = el("ul"); lines.forEach(function (l) {
              ol.appendChild(el("li", {}, [el("span", { text: l.it.qty + " x " + l.p.title + (l.v ? " (" + l.v.name + ")" : "") }), el("span", { text: fmt.format(l.unit * l.it.qty) })]));
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

  count(); shop(); product(); cart();
})();

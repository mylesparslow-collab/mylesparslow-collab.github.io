/* Style switcher: a "Style" dropdown in every portfolio version's top bar.
   Each page loads this with <script src="/assets/site/styles.js" data-v="<key>" defer>.
   Switching keeps your place: same room, same project (#hash). */
(function () {
  var me = document.currentScript || document.querySelector('script[src*="styles.js"][data-v]');
  var cur = me && me.getAttribute('data-v');
  if (!cur) return;

  var V = [
    { k: 'i', name: 'Transit Map', base: '/' },
    { k: 'h', name: 'Orbit', base: '/mockup-h/' },
    { k: 'g', name: 'Sticker Wall', base: '/mockup-g/' },
    { k: 'f', name: 'Plain Web', base: '/mockup-f/' },
    { k: 'e', name: 'Case File', base: '/mockup-e/' },
    { k: 'd', name: 'MPWP 5.1', base: '/mockup-d/' },
    { k: 'c', name: 'The Museum', base: '/mockup-c/' },
    { k: 'b', name: 'Five Rooms', base: '/mockup-b/' }
  ];
  var ROOMS = ['legal', 'business', 'creative', 'design', 'research'];

  // where the dropdown goes in each version's top bar
  var MOUNT = {
    i: ['.bar__in', 'append'], h: ['.bar__in', 'afterfirst'], g: ['header.topbar .bar', 'append'],
    f: ['#top', 'f'], e: ['header.tabrow', 'append'], d: ['nav.fkeys', 'prepend'],
    c: ['.wf__in', 'append'], b: ['.chrome .c.tr', 'prepend']
  };

  function room() {
    var segs = location.pathname.split('/');
    for (var i = segs.length - 1; i >= 0; i--) if (ROOMS.indexOf(segs[i]) > -1) return segs[i];
    return '';
  }
  function target(v) {
    var r = room();
    return v.base + (r ? r + '/index.html' : 'index.html') + location.hash;
  }

  var css = document.createElement('style');
  css.textContent =
    '.ss{display:inline-flex;align-items:center;gap:.45em;font:inherit;color:inherit;white-space:nowrap;flex:none}' +
    '.ss__l{font:inherit;opacity:.75}' +
    '.ss select{font:inherit;color:inherit;background-color:transparent;border:1px solid currentColor;border-radius:999px;' +
    'padding:.28em 1.9em .28em .75em;margin:0;cursor:pointer;-webkit-appearance:none;appearance:none;' +
    'background-image:linear-gradient(45deg,transparent 50%,currentColor 50%),linear-gradient(135deg,currentColor 50%,transparent 50%);' +
    'background-position:calc(100% - 13px) 54%,calc(100% - 8.5px) 54%;background-size:4.5px 4.5px;background-repeat:no-repeat}' +
    '.ss select:focus-visible{outline:2px solid currentColor;outline-offset:2px}' +
    '.ss option{color:#111;background:#fff}' +
    '.ss--i{margin-left:auto}.ss--h{margin-left:12px;margin-right:auto}.ss--e{margin-left:auto;align-self:center;padding:0 12px}' +
    '.ss--d{margin-right:8px}.ss--d select{border-radius:0;padding:.05em 1.7em .05em .5em}' +
    '.ss--f{display:inline-flex}.ss--f select{border-radius:3px}' +
    '.ss--c{margin-left:12px}.ss--g{margin-left:6px}.ss--b{margin-right:8px}' +
    '.ss{position:relative}' +
    /* phones: a compact icon button that opens the same native picker */
    '@media (max-width:640px){.ss{gap:0;margin-left:6px}.ss--i,.ss--h,.ss--e,.ss--d{margin-right:8px}' +
    '.ss__l{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}' +
    '.ss select{width:36px;height:32px;padding:0;color:transparent;background-image:none;border-radius:999px}' +
    '.ss--d select{width:32px;height:24px;border-radius:0}' +
    '.ss::after{content:"";position:absolute;right:0;top:0;bottom:0;width:36px;margin:auto 0;height:16px;background:currentColor;pointer-events:none;' +
    '-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E%3Cpath d=%27M8 1 1 4.5 8 8l7-3.5z%27/%3E%3Cpath d=%27m1 8 7 3.5L15 8M1 11.5 8 15l7-3.5%27 fill=%27none%27 stroke=%27%23000%27 stroke-width=%271.6%27 stroke-linejoin=%27round%27/%3E%3C/svg%3E") center/16px no-repeat;' +
    'mask:url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E%3Cpath d=%27M8 1 1 4.5 8 8l7-3.5z%27/%3E%3Cpath d=%27m1 8 7 3.5L15 8M1 11.5 8 15l7-3.5%27 fill=%27none%27 stroke=%27%23000%27 stroke-width=%271.6%27 stroke-linejoin=%27round%27/%3E%3C/svg%3E") center/16px no-repeat}' +
    '.ss--d::after{width:32px}' +
    /* Orbit: on narrow phones the Home button shows just its house icon, so all five room chips still fit */
    '}@media (max-width:420px){.homebtn>span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.ss--h{margin-left:6px}}';
  document.head.appendChild(css);

  function build() {
    var lab = document.createElement('label');
    lab.className = 'ss ss--' + cur;
    var sp = document.createElement('span');
    sp.className = 'ss__l';
    sp.textContent = 'Style';
    var sel = document.createElement('select');
    sel.setAttribute('aria-label', 'Switch portfolio style');
    V.forEach(function (v) {
      var o = document.createElement('option');
      o.value = v.k;
      o.textContent = v.name + (v.k === 'i' ? ' (live)' : '');
      if (v.k === cur) o.selected = true;
      sel.appendChild(o);
    });
    var all = document.createElement('option');
    all.value = 'all';
    all.textContent = 'All styles…';
    sel.appendChild(all);
    sel.addEventListener('change', function () {
      if (sel.value === 'all') { location.href = '/styles/'; return; }
      for (var i = 0; i < V.length; i++) if (V[i].k === sel.value) { location.href = target(V[i]); return; }
    });
    // don't let the version's own letter shortcuts fire while the menu has focus
    sel.addEventListener('keydown', function (e) { e.stopPropagation(); });
    lab.appendChild(sp);
    lab.appendChild(sel);
    return lab;
  }

  function mount() {
    var m = MOUNT[cur], el = m && document.querySelector(m[0]);
    var node = build();
    if (!el) {                       // fallback: a small line at the top of the page
      var p = document.createElement('p');
      p.style.cssText = 'margin:0;padding:8px 16px;text-align:right';
      p.appendChild(node);
      document.body.insertBefore(p, document.body.firstChild);
      return;
    }
    if (m[1] === 'f') {              // Plain Web: inline in the breadcrumb line, or its own line on the homepage
      var para = el.querySelector('p');
      if (para) { para.appendChild(document.createTextNode('  ·  ')); para.appendChild(node); }
      else { var q = document.createElement('p'); q.appendChild(node); el.insertBefore(q, el.firstChild); }
    } else if (m[1] === 'prepend') el.insertBefore(node, el.firstChild);
    else if (m[1] === 'afterfirst') el.insertBefore(node, el.firstElementChild ? el.firstElementChild.nextSibling : null);
    else el.appendChild(node);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();

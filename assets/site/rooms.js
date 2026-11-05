/* Mockup B room pages: the bits the homepage does not need. b.js (theme, chrome, menu, curtain, reveals) runs first. */
(function () {
  'use strict';
  /* before / after sliders (the same range-input pattern as the live pages; works with the keyboard) */
  Array.prototype.forEach.call(document.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });
})();

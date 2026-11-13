// Keyboard, mouse-drag orbit, touch joystick + jump button, optional gamepad.
export class Input {
  constructor(canvas) {
    this.canvas = canvas;
    this.keys = new Set();
    this.stick = { x: 0, y: 0, id: null }; // y: up is positive
    this.jumpQueued = false;
    this.orbit = { dx: 0, dy: 0, active: false, last: 0 };
    this.touchUI = false;
    this.enabled = true;
    this.onGesture = () => {};
    const stickEl = document.getElementById('stick'), knob = document.getElementById('knob'), jumpEl = document.getElementById('jumpBtn');

    addEventListener('keydown', (e) => {
      this.onGesture();
      // Space on a focused button inside a card (picker card, Start, Play again) activates it; during play it still jumps
      const onButton = e.code === 'Space' && e.target instanceof Element && e.target.closest('.card button');
      if (onButton) return;
      if (e.repeat) { if (e.code === 'Space') e.preventDefault(); return; }
      this.keys.add(e.code);
      if (e.code === 'Space') { this.jumpQueued = true; e.preventDefault(); }
      if (e.code.startsWith('Arrow')) e.preventDefault();
    });
    addEventListener('keyup', (e) => this.keys.delete(e.code));
    addEventListener('blur', () => this.keys.clear());

    // mouse / touch drag on the canvas orbits the camera
    const drags = new Map();
    canvas.addEventListener('pointerdown', (e) => {
      this.onGesture();
      drags.set(e.pointerId, { x: e.clientX, y: e.clientY });
      this.orbit.active = true;
      try { canvas.setPointerCapture(e.pointerId); } catch (_) { /* ignore */ }
    });
    canvas.addEventListener('pointermove', (e) => {
      const d = drags.get(e.pointerId);
      if (!d) return;
      this.orbit.dx += e.clientX - d.x; this.orbit.dy += e.clientY - d.y;
      d.x = e.clientX; d.y = e.clientY; this.orbit.last = performance.now();
    });
    const end = (e) => { drags.delete(e.pointerId); if (!drags.size) this.orbit.active = false; };
    canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());

    // virtual joystick
    const R = 55;
    const moveStick = (e) => {
      const r = stickEl.getBoundingClientRect();
      let dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
      const l = Math.hypot(dx, dy);
      if (l > R) { dx = dx / l * R; dy = dy / l * R; }
      this.stick.x = dx / R; this.stick.y = -dy / R;
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
    };
    stickEl.addEventListener('pointerdown', (e) => {
      this.onGesture(); this.stick.id = e.pointerId; stickEl.setPointerCapture(e.pointerId); moveStick(e); e.preventDefault();
    });
    stickEl.addEventListener('pointermove', (e) => { if (e.pointerId === this.stick.id) moveStick(e); });
    const stickEnd = (e) => {
      if (e.pointerId !== this.stick.id) return;
      this.stick.id = null; this.stick.x = this.stick.y = 0; knob.style.transform = 'translate(0,0)';
    };
    stickEl.addEventListener('pointerup', stickEnd); stickEl.addEventListener('pointercancel', stickEnd);
    jumpEl.addEventListener('pointerdown', (e) => { this.onGesture(); this.jumpQueued = true; jumpEl.classList.add('down'); e.preventDefault(); });
    const jumpUp = () => jumpEl.classList.remove('down');
    jumpEl.addEventListener('pointerup', jumpUp); jumpEl.addEventListener('pointercancel', jumpUp);

    const showTouch = () => { if (!this.touchUI) { this.touchUI = true; document.body.classList.add('touch'); } };
    if (matchMedia('(pointer: coarse)').matches) showTouch();
    addEventListener('touchstart', showTouch, { passive: true, once: true });
    this._padJump = false;
  }

  // returns {x, y, mag, run}: x right, y forward (camera-relative), mag 0..1
  read() {
    let x = 0, y = 0, run = false, mag = 0;
    if (this.enabled) {
      const k = this.keys;
      x = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
      y = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
      run = k.has('ShiftLeft') || k.has('ShiftRight');
      let l = Math.hypot(x, y);
      if (l > 0) { x /= l; y /= l; mag = run ? 1 : 0.5; }
      // touch stick: push far = run
      const sl = Math.hypot(this.stick.x, this.stick.y);
      if (sl > 0.12) { x = this.stick.x / sl; y = this.stick.y / sl; mag = sl > 0.8 ? 1 : Math.min(0.5, sl * 0.6); run = sl > 0.8; }
      // gamepad
      const pads = navigator.getGamepads ? navigator.getGamepads() : [];
      for (const p of pads) {
        if (!p) continue;
        const gx = p.axes[0] || 0, gy = -(p.axes[1] || 0), gl = Math.hypot(gx, gy);
        if (gl > 0.2) { x = gx / gl; y = gy / gl; run = gl > 0.8 || p.buttons[7]?.pressed || p.buttons[1]?.pressed; mag = run ? 1 : 0.5; }
        const j = !!p.buttons[0]?.pressed;
        if (j && !this._padJump) this.jumpQueued = true;
        this._padJump = j;
        const rx = p.axes[2] || 0, ry = p.axes[3] || 0;
        if (Math.abs(rx) > 0.2 || Math.abs(ry) > 0.2) { this.orbit.dx += rx * 6; this.orbit.dy += ry * 4; this.orbit.last = performance.now(); }
        break;
      }
    }
    return { x, y, mag, run };
  }
  takeJump() { const j = this.jumpQueued; this.jumpQueued = false; return this.enabled && j; }
  takeOrbit() { const o = { dx: this.orbit.dx, dy: this.orbit.dy }; this.orbit.dx = this.orbit.dy = 0; return o; }
}

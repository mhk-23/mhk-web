(() => {
  /* ---------- tweak here ---------- */
  const CONFIG = {
    pauseMs: 300,         // empty black screen before anything happens
    hissMs: 250,          // aerosol mist only, before paint lands
    handSpeed: 7.2,       // how fast the hand moves. Lower = slower, longer animation
    hopWeight: 20,        // time cost of lifting the can between strokes (higher = longer pause)
    endSlow: 0.45,        // strokes start and finish slower (1 = constant speed)
    settleMs: 350,        // final pass: faint overspray settles into the exact artwork
    tailMs: 250,          // lets the final mist clear
    paintAlpha: 0.92,     // strength of each spray puff
    brushSize: 3.8,       // spray width relative to the letter's thickness (bigger = softer, wider spill)
    stampSpacing: 0.065,   // puffs per stroke length (lower = denser, heavier)
    handSmoothMs: 3,      // small = follows the stroke exactly
    softMist: 2,          // soft mist puffs per frame
    specks: 7             // tiny flying paint specks per frame
  };

  /* Strokes traced from the artwork itself: letter by letter, each stroke = [x, y, brushRadius, ...] in 2048px space.
     Brush radius follows how thick the letter is at that point. */
  const STROKES = __STROKES__;

  const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
  const art = document.getElementById("art");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const rnd = Math.random, gauss = () => rnd() + rnd() + rnd() + rnd() - 2;
  const ease = x => x * x * (3 - 2 * x);
  // everything lives in the artwork's own pixel space, so resizing never restarts or breaks it
  let dpr = 1, W = 0, H = 0, ax = 0, ay = 0, aw = 0, ah = 0, MW = 2048, MH = 728;
  let mask, mctx, legs = [], Wtot = 0, SPRAY = 3500, li = 0, parts = [], stamps = [], mistSprite;
  let done = false, last = 0, T = 0, hand = null, kPrev = 0, canOn = false;

  function finish() {                       // show the untouched PNG, drop the canvas
    if (done) return; done = true;
    art.style.opacity = 1; cv.style.display = "none";
  }

  /* a pre-rendered puff of spray: dense in the middle, grainy and thin at the edge */
  function makeStamp(S) {
    const c = document.createElement("canvas"); c.width = c.height = S;
    const g = c.getContext("2d"); g.fillStyle = "#fff"; const rm = S / 2 - 1;
    for (let n = 0, N = Math.round(S * S * .05); n < N;) {
      const r = rm * Math.sqrt(rnd());
      if (rnd() > 1 - (r / rm) ** 2) continue;
      const a = rnd() * 6.283, d = 1.2 + rnd() * 2.4;
      g.globalAlpha = .3 + rnd() * .7;
      g.fillRect(S / 2 + Math.cos(a) * r, S / 2 + Math.sin(a) * r, d, d); n++;
    }
    return c;
  }
  function makeMist() {
    const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
    const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, "rgba(226,232,255,.6)"); gr.addColorStop(1, "rgba(226,232,255,0)");
    g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return c;
  }

  /* where the artwork currently sits on screen (re-read every frame, so any resize just works) */
  function place() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    W = Math.round(innerWidth * dpr); H = Math.round(innerHeight * dpr);
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    const r = art.getBoundingClientRect();
    ax = r.left * dpr; ay = r.top * dpr; aw = r.width * dpr; ah = r.height * dpr;
  }

  /* turn the strokes into one timeline: write a stroke, lift, move, write the next */
  function plan() {
    const f = MW / 2048; let px = null, py = 0, pr = 0;
    for (const st of STROKES) {
      const p = st.p, n = p.length / 3;
      if (n < 2) continue;
      const x0 = p[0] * f, y0 = p[1] * f, r0 = p[2] * f;
      if (px !== null) legs.push({ x0: px, y0: py, r0: pr, x1: x0, y1: y0, r1: r0, on: false, w: CONFIG.hopWeight + Math.hypot(x0 - px, y0 - py) * .2 });
      let L = 0; for (let j = 1; j < n; j++) L += Math.hypot(p[j * 3] - p[j * 3 - 3], p[j * 3 + 1] - p[j * 3 - 2]) * f;
      let acc = 0;
      for (let j = 1; j < n; j++) {
        const xa = p[j * 3 - 3] * f, ya = p[j * 3 - 2] * f, xb = p[j * 3] * f, yb = p[j * 3 + 1] * f, len = Math.hypot(xb - xa, yb - ya);
        const s = (acc + len / 2) / L, v = CONFIG.endSlow + (1 - CONFIG.endSlow) * Math.sin(Math.PI * s);   // slow at the ends, quick in the middle
        legs.push({ x0: xa, y0: ya, r0: p[j * 3 - 1] * f, x1: xb, y1: yb, r1: p[j * 3 + 2] * f, on: true, w: len / v });
        acc += len;
      }
      px = p[n * 3 - 3] * f; py = p[n * 3 - 2] * f; pr = p[n * 3 - 1] * f;
    }
    let acc = 0; for (const l of legs) { l.c = acc; acc += l.w; } Wtot = acc;
    SPRAY = Wtot / CONFIG.handSpeed;
  }

  function nozzle(u) {                       // raw hand position + brush size at u = 0..1 through the whole spray
    const w = u * Wtot;
    while (li < legs.length - 1 && w >= legs[li].c + legs[li].w) li++;
    const l = legs[li], f = Math.min(1, Math.max(0, (w - l.c) / l.w));
    return { x: l.x0 + (l.x1 - l.x0) * f, y: l.y0 + (l.y1 - l.y0) * f, r: l.r0 + (l.r1 - l.r0) * f, on: l.on };
  }

  function spawn(pos, hiss, spraying, dt) {
    const R = Math.max(18, pos.r), cnt = r => { const n = r * dt / 16.7; return (n | 0) + (rnd() < n % 1 ? 1 : 0); };
    for (let k = cnt(CONFIG.softMist); k > 0; k--) if (rnd() < hiss) {
      const a = rnd() * 6.283, d = R * Math.sqrt(rnd()) * 1.2;
      parts.push({ type: 0, x: pos.x + Math.cos(a) * d, y: pos.y + Math.sin(a) * d, vx: Math.cos(a) * R * .006, vy: Math.sin(a) * R * .006 - R * .001, age: 0, life: 450 + rnd() * 350, s: R * (2 + rnd() * 3), a: .045 });
    }
    if (spraying) for (let k = cnt(CONFIG.specks); k > 0; k--) {
      const a = rnd() * 6.283, d = R * (1 + rnd() * 2.2), v = R * .012 * (rnd() + .3);
      parts.push({ type: 1, x: pos.x + Math.cos(a) * d, y: pos.y + Math.sin(a) * d, vx: Math.cos(a) * v, vy: Math.sin(a) * v, age: 0, life: 220 + rnd() * 300, s: R * (.03 + rnd() * .05), a: .55, c: rnd() < .25 ? "#ff7ab6" : "#e6ecff" });
    }
  }
  function drawParts(dt) {
    const sx = aw / MW;
    for (let i = parts.length - 1; i >= 0; i--) {
      const p = parts[i]; p.age += dt;
      if (p.age >= p.life) { parts.splice(i, 1); continue; }
      p.x += p.vx * dt / 16.7; p.y += p.vy * dt / 16.7;
      const X = ax + p.x * sx, Y = ay + p.y * sx;
      ctx.globalAlpha = p.a * (1 - p.age / p.life);
      if (p.type === 0) { const s = p.s * sx; ctx.drawImage(mistSprite, X - s / 2, Y - s / 2, s, s); }
      else { const s = Math.max(dpr, p.s * sx); ctx.fillStyle = p.c; ctx.fillRect(X, Y, s, s); }
    }
    ctx.globalAlpha = 1;
  }

  function loop(now) {
    if (done) return;
    const dt = Math.max(0, Math.min(now - last, 40)); last = now;
    requestAnimationFrame(loop);
    place();
    if (document.hidden || aw < 8) return;                        // the clock only runs while the page can actually be seen
    T += dt;
    const t = T, sp0 = CONFIG.pauseMs + CONFIG.hissMs, sp1 = sp0 + SPRAY, end = sp1 + CONFIG.settleMs;
    if (t >= end + CONFIG.tailMs) return finish();
    ctx.clearRect(0, 0, W, H);
    if (t < CONFIG.pauseMs) return;                               // pure black

    if (!hand) { const p0 = nozzle(0); hand = { x: p0.x, y: p0.y, r: p0.r }; }
    if (t < sp0) {                                                // hiss: mist only, can resting at the start of the first stroke
      spawn(hand, ease((t - CONFIG.pauseMs) / CONFIG.hissMs), false, dt);
    } else if (t < sp1 + 60) {
      const SUB = 6, k = 1 - Math.exp(-(dt / SUB) / CONFIG.handSmoothMs);
      mctx.globalAlpha = CONFIG.paintAlpha;
      for (let s = 1; s <= SUB; s++) {                            // several small hand steps per frame keep the line smooth
        const tt = t - dt + dt * s / SUB, raw = nozzle(Math.min(1, Math.max(0, (tt - sp0) / SPRAY)));
        const ox = hand.x, oy = hand.y;
        hand.x += (raw.x - hand.x) * k; hand.y += (raw.y - hand.y) * k; hand.r += (raw.r - hand.r) * k;
        canOn = raw.on;
        if (!raw.on) continue;                                    // can lifted between strokes
        const n = Math.min(14, Math.max(1, Math.ceil(Math.hypot(hand.x - ox, hand.y - oy) / Math.max(1.5, hand.r * CONFIG.stampSpacing))));
        for (let j = 0; j < n; j++) {                             // puffs laid down evenly along the stroke
          const q = (j + 1) / n, x = ox + (hand.x - ox) * q + gauss() * hand.r * .06, y = oy + (hand.y - oy) * q + gauss() * hand.r * .06;
          const a = rnd() * 6.283, c = Math.cos(a), sn = Math.sin(a), size = hand.r * CONFIG.brushSize * (.9 + rnd() * .2);   // wide where the letter is thick
          mctx.setTransform(c, sn, -sn, c, x, y);
          mctx.drawImage(stamps[(rnd() * stamps.length) | 0], -size / 2, -size / 2, size, size);
        }
      }
      mctx.setTransform(1, 0, 0, 1, 0, 0); mctx.globalAlpha = 1;
      spawn(hand, 1, t < sp1, dt);
    }
    if (t >= sp1 && kPrev < 1) {                                  // end: faint overspray settles into the exact artwork
      const k = ease(Math.min(1, (t - sp1) / CONFIG.settleMs));
      mctx.fillStyle = "#fff"; mctx.globalAlpha = k >= 1 ? 1 : 1 - (1 - k) / (1 - kPrev);
      mctx.fillRect(0, 0, MW, MH); mctx.globalAlpha = 1; kPrev = k;
    }

    ctx.globalCompositeOperation = "source-over";                 // artwork, kept only where paint has landed
    ctx.drawImage(art, ax, ay, aw, ah);
    ctx.globalCompositeOperation = "destination-in";
    ctx.drawImage(mask, ax, ay, aw, ah);
    ctx.globalCompositeOperation = "source-over";
    drawParts(dt);
    if (canOn && t >= sp0 && t < sp1 + 60) {                      // the spray can itself: a soft aerosol cloud that travels with the nozzle
      const sx = aw / MW, s = Math.max(26, hand.r * 4.2) * sx;
      ctx.globalAlpha = .17; ctx.drawImage(mistSprite, ax + hand.x * sx - s / 2, ay + hand.y * sx - s / 2, s, s); ctx.globalAlpha = 1;
    }
  }

  function start() {
    try {
      MW = art.naturalWidth || 2048; MH = art.naturalHeight || 728;
      mask = document.createElement("canvas"); mask.width = MW; mask.height = MH; mctx = mask.getContext("2d");
      plan();
      if (!legs.length) return finish();
      stamps = [0, 1, 2, 3, 4, 5].map(() => makeStamp(128));
      mistSprite = makeMist();
      last = performance.now(); requestAnimationFrame(loop);
    } catch (e) { finish(); }
  }

  if (reduce) finish();
  else (art.decode ? art.decode() : Promise.resolve()).then(start, finish);   // the clock only runs while the landing page is on screen
})();

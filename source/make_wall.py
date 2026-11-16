import random, math, json

# ---- the thirteen pieces. d = desktop layout (cx, cy, width of longest line, font size, tilt), m = phone layout ----
P = [
 dict(slug='tea-party-gone-wrong', name='Tea Party Gone Wrong', lines=['TEA PARTY', 'GONE WRONG'], font='Titan One', adv=.62, style='bubble',
      F='#ff5aa8', O='#3a0b36', E='#8a1a63', glow='#ff5aa8', drips=4, d=(360, 372, 600, 135, -4), m=(400, 345, 640, 145, -3)),
 dict(slug='slow-state', name='Slow State', lines=['SLOW STATE'], font='Chango', adv=.78, style='bubble',
      F='#46c4f2', O='#2b1a7a', E='#1b2f7a', glow='#46c4f2', drips=3, d=(980, 400, 640, 105, 2), m=(400, 610, 680, 112, 2)),
 dict(slug='eka-lakhani', name='Eka Lakhani', lines=['Eka Lakhani'], font='Knewave', adv=.46, style='script',
      F='#ec2a3c', O='#7a0f1d', E='#7a0f1d', glow='#ec2a3c', drips=2, d=(1250, 140, 560, 120, -5), m=(400, 100, 600, 128, -5)),
 dict(slug='comet-x-subway-surfers', name='Comet x Subway Surfers', lines=['COMET X', 'SUBWAY', 'SURFERS'], font='Luckiest Guy', adv=.55, style='block',
      F='#ff8a1f', O='#3a1405', E='#00a7c4', glow='#ff8a1f', drips=2, d=(250, 126, 330, 85, -3), m=(230, 840, 330, 85, -3)),
 dict(slug='delhi-travel-guide', name='Delhi Travel Guide', lines=['DELHI', 'TRAVEL GUIDE'], font='Permanent Marker', adv=.55, style='marker',
      F='#ffffff', O='#e0267d', E='#e0267d', glow='#ff4fa3', drips=3, d=(700, 125, 360, 58, 1), m=(590, 800, 320, 52, 2)),
 dict(slug='the-label-jenn', name='The Label Jenn', lines=['The Label', 'Jenn'], font='Knewave', adv=.46, style='script',
      F='#ffffff', O='#ff2f92', E='#ff2f92', glow='#ff2f92', drips=2, d=(1418, 375, 330, 95, -8), m=(560, 1180, 330, 95, -7)),
 dict(slug='the-appetite', name='The Appetite', lines=['THE APPETITE'], font='Titan One', adv=.62, style='bubble',
      F='#ffc20e', O='#0b2a5b', E='#e86a10', glow='#ffc20e', drips=3, d=(600, 645, 700, 110, -2), m=(400, 1020, 720, 112, -2)),
 dict(slug='hippies-x-y2k', name='Hippies x Y2K', lines=['HIPPIES X Y2K'], font='Permanent Marker', adv=.55, style='marker',
      F='#39ff88', O='#0d3b2a', E='#0d3b2a', glow='#39ff88', drips=3, d=(1100, 560, 380, 58, 3), m=(205, 1170, 330, 50, 3)),
 dict(slug='ms-bean', name='Ms Bean', lines=['MS', 'BEAN'], font='Bowlby One', adv=.70, style='block',
      F='#b784f0', O='#3a0f29', E='#5c1d42', glow='#b784f0', drips=0, d=(190, 835, 300, 150, 0), m=(200, 1400, 300, 150, 0)),
 dict(slug='tupperware', name='Tupperware', lines=['TUPPERWARE'], font='Chango', adv=.78, style='bubble',
      F='#ff6a2b', O='#4a1208', E='#9c2a0a', glow='#ff6a2b', drips=3, d=(640, 865, 560, 92, 1), m=(400, 1640, 640, 105, 1)),
 dict(slug='killer-jeans', name='Killer Jeans', lines=['KILLER', 'JEANS'], font='Luckiest Guy', adv=.55, style='block',
      F='#c8ff2e', O='#101010', E='#ff2f92', glow='#c8ff2e', drips=2, d=(1070, 790, 360, 120, 2), m=(580, 1400, 360, 120, 2)),
 dict(slug='strange-studio', name='Strange Studio', lines=['STRANGE', 'STUDIO'], font='Bowlby One', adv=.70, style='block',
      F='#19b8a8', O='#06293a', E='#0f4f63', glow='#19b8a8', drips=0, d=(1410, 815, 340, 75, -2), m=(210, 1780, 340, 78, -2)),
 dict(slug='ss-2030-trendbook', name='SS 2030 Trendbook', lines=['SS 2030', 'TRENDBOOK'], font='Bangers', adv=.46, style='block',
      F='#7b6bff', O='#120f4a', E='#3b2fb5', glow='#7b6bff', drips=0, d=(1425, 560, 330, 80, 2), m=(600, 1780, 330, 80, 2)),
]
FONTSTACK = {'Titan One': 'Titan One, Arial Black, Impact, sans-serif', 'Chango': 'Chango, Arial Black, Impact, sans-serif', 'Knewave': 'Knewave, Brush Script MT, cursive',
             'Permanent Marker': 'Permanent Marker, Marker Felt, Comic Sans MS, cursive', 'Bowlby One': 'Bowlby One, Arial Black, Impact, sans-serif',
             'Luckiest Guy': 'Luckiest Guy, Impact, Arial Black, sans-serif', 'Bangers': 'Bangers, Impact, Arial Black, sans-serif'}
STYLE = {  # outline width, white halo extra, extrusion steps and offset (all as a share of the font size)
 'bubble': dict(ow=.11, halo=.15, steps=4, dx=.018, dy=.026, hatch=True),
 'script': dict(ow=.07, halo=.20, steps=0, dx=0, dy=0, hatch=False),
 'block':  dict(ow=.08, halo=.10, steps=7, dx=.022, dy=.03, hatch=True),
 'marker': dict(ow=.07, halo=.12, steps=0, dx=0, dy=0, hatch=False),
}

def geom(p, lay):
    cx, cy, W, fs, r = p[lay]; n = max(len(l) for l in p['lines']); c = W / (n * p['adv'] * fs); lh = fs * .92; k = len(p['lines'])
    lines = [(t, (i - (k - 1) / 2) * lh, c * p['adv'] * fs * len(t)) for i, t in enumerate(p['lines'])]
    return dict(cx=cx, cy=cy, W=W, fs=fs, r=r, c=c, lines=lines, h=k * lh, lh=lh)

def bbox(p, lay):
    g = geom(p, lay); w = max(l[2] for l in g['lines']); a = math.radians(g['r']); hw, hh = w / 2, g['h'] / 2
    ex = abs(hw * math.cos(a)) + abs(hh * math.sin(a)); ey = abs(hw * math.sin(a)) + abs(hh * math.cos(a)); return (g['cx'] - ex, g['cy'] - ey, g['cx'] + ex, g['cy'] + ey)

def overlaps(lay, W, H, thr=.12):
    out = []; ids = range(len(P))
    for a in ids:
        A = bbox(P[a], lay)
        if A[0] < 0 or A[1] < 0 or A[2] > W or A[3] > H: out.append(('off', P[a]['slug'], [round(v) for v in A]))
        for b in range(a + 1, len(P)):
            B = bbox(P[b], lay); ox = min(A[2], B[2]) - max(A[0], B[0]); oy = min(A[3], B[3]) - max(A[1], B[1])
            if ox > 0 and oy > 0:
                share = ox * oy / min((A[2] - A[0]) * (A[3] - A[1]), (B[2] - B[0]) * (B[3] - B[1]))
                if share > thr: out.append((P[a]['slug'], P[b]['slug'], round(share, 2)))
    return out

DECOR = {  # non-letter wall details: sparkles, rings, scribbled crosses, swooshes (x, y, size)
 'd': dict(spark=[(60, 330, 34), (720, 480, 30), (1330, 250, 40), (830, 260, 26), (950, 700, 28), (80, 650, 30), (1520, 700, 34), (520, 560, 22)],
           ring=[(1450, 250, 70, '#ff4fa3'), (250, 560, 60, '#46c4f2'), (880, 940, 80, '#ffc20e')],
           cross=[(1500, 100, 46, '#7a1457'), (560, 250, 36, '#00a7c4'), (1010, 960, 40, '#3b2fb5')]),
 'm': dict(spark=[(60, 230, 30), (740, 470, 28), (740, 960, 30), (50, 1280, 28), (740, 1530, 30), (60, 1720, 26)],
           ring=[(720, 300, 60, '#ff4fa3'), (80, 970, 55, '#46c4f2')], cross=[(740, 80, 40, '#7a1457'), (60, 1500, 36, '#3b2fb5')]),
}
BLOBS = {  # soft spray colour fields behind the lettering (cx, cy, rx, ry, colour, strength)
 'd': [(360, 350, 430, 260, '#ff5aa8', .55), (980, 400, 470, 210, '#46c4f2', .55), (1250, 140, 380, 150, '#ec2a3c', .38), (250, 130, 280, 170, '#ff8a1f', .42),
       (600, 645, 480, 170, '#ffc20e', .48), (190, 845, 230, 200, '#b784f0', .5), (1085, 790, 330, 210, '#c8ff2e', .38), (640, 865, 360, 120, '#ff6a2b', .38),
       (1390, 805, 250, 150, '#19b8a8', .45), (1425, 560, 260, 140, '#7b6bff', .42), (1100, 560, 280, 90, '#39ff88', .35), (1430, 375, 250, 130, '#ff2f92', .38)],
 'm': [(400, 330, 460, 250, '#ff5aa8', .55), (400, 610, 470, 160, '#46c4f2', .55), (400, 120, 400, 120, '#ec2a3c', .38), (230, 840, 220, 150, '#ff8a1f', .42),
       (400, 1020, 470, 150, '#ffc20e', .48), (200, 1400, 220, 190, '#b784f0', .5), (580, 1400, 250, 190, '#c8ff2e', .38), (400, 1640, 440, 130, '#ff6a2b', .38),
       (210, 1780, 240, 110, '#19b8a8', .45), (600, 1780, 240, 110, '#7b6bff', .42), (560, 1180, 240, 120, '#ff2f92', .38), (200, 1170, 220, 70, '#39ff88', .35)],
}
ORDER = ['tea-party-gone-wrong', 'slow-state', 'the-appetite', 'tupperware', 'ms-bean', 'killer-jeans', 'comet-x-subway-surfers', 'eka-lakhani', 'strange-studio',
         'ss-2030-trendbook', 'the-label-jenn', 'hippies-x-y2k', 'delhi-travel-guide']

def sparkle(x, y, s, col='#fff'):
    return (f'<path d="M{x} {y - s}Q{x} {y} {x + s * .8} {y}Q{x} {y} {x} {y + s}Q{x} {y} {x - s * .8} {y}Q{x} {y} {x} {y - s}Z" fill="{col}" stroke="#222" stroke-width="2.5" stroke-linejoin="round"/>')

def build_svg(lay, cls, pfx):
    W, H = (1600, 1000) if lay == 'd' else (800, 1900); rnd = random.Random(11 if lay == 'd' else 12)
    defs = ['<filter id="%srough" x="-8%%" y="-25%%" width="116%%" height="150%%"><feTurbulence type="fractalNoise" baseFrequency=".035 .05" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="4.5"/></filter>' % pfx,
            '<filter id="%shaze" x="-20%%" y="-60%%" width="140%%" height="220%%"><feGaussianBlur stdDeviation="14"/></filter>' % pfx,
            '<filter id="%sstip" x="0" y="0" width="100%%" height="100%%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="9" result="n"/><feComposite in="SourceGraphic" in2="n" operator="arithmetic" k1="2.1" k2="0" k3="0" k4="0"/></filter>' % pfx,
            '<pattern id="%shatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(-38)"><line x1="0" y1="0" x2="0" y2="10" stroke="#fff" stroke-opacity=".30" stroke-width="3.4"/></pattern>' % pfx]
    for i, (cx, cy, rx, ry, col, a) in enumerate(BLOBS[lay]):
        defs.append(f'<radialGradient id="{pfx}b{i}"><stop offset="0" stop-color="{col}" stop-opacity="{a}"/><stop offset=".55" stop-color="{col}" stop-opacity="{a * .55:.2f}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
    body = [f'<g filter="url(#{pfx}stip)">' + ''.join(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{pfx}b{i})"/>' for i, (cx, cy, rx, ry, col, a) in enumerate(BLOBS[lay])) + '</g>']
    dc = DECOR[lay]
    body += [f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r * .45:.0f}" transform="rotate(-18 {x} {y})" fill="none" stroke="{c}" stroke-width="7" stroke-opacity=".75" stroke-linecap="round"/>' for x, y, r, c in dc['ring']]
    body += [f'<g stroke="{c}" stroke-width="{s * .32:.0f}" stroke-linecap="round" opacity=".85"><path d="M{x - s} {y - s}L{x + s} {y + s}M{x + s} {y - s}L{x - s} {y + s}"/></g>' for x, y, s, c in dc['cross']]
    for slug in ORDER:
        p = next(q for q in P if q['slug'] == slug); g = geom(p, lay); st = STYLE[p['style']]; fs = g['fs']; ow = fs * st['ow']; ff = FONTSTACK[p['font']]
        ids = []
        for k, (t, yo, lw) in enumerate(g['lines']):
            tid = f'{pfx}{slug}-{k}'; ids.append(tid)
            defs.append(f'<text id="{tid}" x="0" y="{yo:.1f}" dy=".35em" text-anchor="middle" font-family="{ff}" font-size="{fs}" textLength="{lw:.1f}" lengthAdjust="spacingAndGlyphs">{t}</text>')
        uses = ''.join(f'<use href="#{i}"/>' for i in ids)
        lay_ = []
        lay_.append(f'<g filter="url(#{pfx}haze)" opacity=".45" fill="{p["F"]}" stroke="{p["F"]}" stroke-width="{fs * .30:.1f}" stroke-linejoin="round">{uses}</g>')               # spray haze
        lay_.append(f'<g fill="#fff" stroke="#fff" stroke-width="{ow + fs * st["halo"]:.1f}" stroke-linejoin="round">{uses}</g>')                                                         # white halo, the "buff"
        for s in range(st['steps'], 0, -1):
            lay_.append(f'<g transform="translate({s * st["dx"] * fs:.1f} {s * st["dy"] * fs:.1f})" fill="{p["E"]}" stroke="{p["E"]}" stroke-width="{ow:.1f}" stroke-linejoin="round">{uses}</g>')   # 3D extrusion
        lay_.append(f'<g fill="{p["O"]}" stroke="{p["O"]}" stroke-width="{ow:.1f}" stroke-linejoin="round">{uses}</g>')                                                                       # dark outline
        last = g['lines'][-1]; y0 = last[1] + fs * .30; half = max(l[2] for l in g['lines']) / 2
        for d in range(p['drips']):
            x = rnd.uniform(-half * .8, half * .8); ln = rnd.uniform(fs * .22, fs * .75); w = fs * rnd.uniform(.035, .06)
            lay_.append(f'<path d="M{x:.1f} {y0:.1f}v{ln:.1f}" stroke="{p["O"]}" stroke-width="{w + ow * .5:.1f}" stroke-linecap="round" fill="none"/><path d="M{x:.1f} {y0:.1f}v{ln:.1f}" stroke="{p["F"]}" stroke-width="{w:.1f}" stroke-linecap="round" fill="none"/>')
        lay_.append(f'<g fill="{p["F"]}">{uses}</g>')                                                                                                                                      # colour fill
        if st['hatch']: lay_.append(f'<g fill="url(#{pfx}hatch)">{uses}</g>')                                                                                                                # marker hatching
        lay_.append(f'<g fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="{fs * .022:.1f}" transform="translate({-fs * .02:.1f} {-fs * .02:.1f})">{uses}</g>')                    # rim light
        specks = []
        for _ in range(26):
            a = rnd.uniform(0, 6.283); rr = rnd.uniform(.5, 1.0); sx = math.cos(a) * (half + fs * .3) * rr; sy = math.sin(a) * (g['h'] / 2 + fs * .35) * rr
            specks.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{rnd.uniform(.9, 3.6):.1f}" fill="{p[rnd.choice(["F", "F", "O"])]}" opacity="{rnd.uniform(.45, .9):.2f}"/>')
        body.append(f'<a class="g" href="#/work/{slug}" style="--glow:{p["glow"]}" aria-label="{p["name"]}"><title>{p["name"]}</title>'
                    f'<g transform="translate({g["cx"]} {g["cy"]}) rotate({g["r"]})"><g class="hov"><g filter="url(#{pfx}rough)">{"".join(lay_)}</g>{"".join(specks)}</g></g></a>')
    for x, y, s in dc['spark']: body.append(sparkle(x, y, s))
    return f'<svg class="wall {cls}" viewBox="0 0 {W} {H}" role="group" aria-label="Projects" xmlns="http://www.w3.org/2000/svg"><defs>{"".join(defs)}</defs>{"".join(body)}</svg>'

if __name__ == '__main__':
    for lay, (W, H) in (('d', (1600, 1000)), ('m', (800, 1900))):
        print(lay, 'compression c per piece:', {p['slug'][:10]: round(geom(p, lay)['c'], 2) for p in P})
        print(lay, 'overlap / off-board report:', overlaps(lay, W, H) or 'none')
    sd, sm = build_svg('d', 'wall-d', 'd-'), build_svg('m', 'wall-m', 'm-')
    open('wall_d.svg.html', 'w').write(sd); open('wall_m.svg.html', 'w').write(sm)
    json.dump({p['slug']: p['name'] for p in P}, open('projects.json', 'w'))
    print('markup size: desktop', len(sd) // 1024, 'KB | phone', len(sm) // 1024, 'KB')

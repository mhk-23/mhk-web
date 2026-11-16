import numpy as np, json, sys
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.graph import route_through_array
from skimage.draw import disk

A = np.array(Image.open('/mnt/user-data/uploads/1791523354597_image.png').convert('RGBA'))[..., 3]
W2, H2 = 1024, 364                                                    # work at half resolution, export at full
a2 = np.array(Image.fromarray(A).resize((W2, H2), Image.BOX)); m = a2 > 120
lab, n = ndi.label(m, structure=np.ones((3, 3))); sz = ndi.sum(m, lab, range(1, n + 1)); m = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= 30])
dt = ndi.distance_transform_edt(m)
COST = np.where(m, 1.0 / (dt + .6) ** 2, 1e4)                          # cheap along the middle of a stroke, very costly off the letter

# ---- how each letter is written: strokes in order, each a list of waypoints (x, y in 2048px space) ----
# a stroke with kind 'drip' is a straight, thin, downward run. Everything else follows the letter between its waypoints.
LETTERS = {
 'P': [  # stem first, top to bottom; then the bowl round and back; then the flick and drips
   ('s', [(72,148),(98,270),(150,385),(205,490),(250,600),(265,660)]),
   ('s', [(92,162),(200,180),(300,208),(372,243),(392,285),(352,350),(272,398),(185,424)]),
   ('s', [(128,384),(52,392)]),
   ('drip', [(80,252),(80,342)]), ('drip', [(122,412),(122,462)]), ('drip', [(141,432),(141,540)]), ('drip', [(158,432),(158,490)])],
 'O': [  # one loop, counter-clockwise from the top
   ('s', [(410,292),(352,330),(342,410),(362,480),(410,520),(470,522),(520,495),(545,440),(530,385),(495,335),(450,305),(410,292)]),
   ('drip', [(418,545),(418,592)])],
 'R': [  # stem down, then the bowl, then the leg (and its long diagonal run under the T)
   ('s', [(512,145),(522,235),(548,300),(578,345)]),
   ('s', [(525,150),(600,172),(670,200),(705,235),(690,290),(640,312),(582,345)]),
   ('s', [(585,350),(640,420),(652,490),(632,555),(616,598)]),
   ('s', [(668,350),(720,383),(800,410),(870,458),(930,515),(985,578)]),
   ('drip', [(722,285),(722,345)]), ('drip', [(771,458),(771,568)]), ('drip', [(781,458),(781,500)])],
 'T': [  # the crossbar left to right, then the stem down from the spike
   ('s', [(702,208),(800,200),(900,190),(1000,172),(1100,166),(1185,160)]),
   ('s', [(945,125),(930,200),(940,290),(960,380),(980,470),(990,560),(985,600)])],
 'F': [  # stem down, then the top bar left to right, then the shorter middle bar
   ('s', [(1030,320),(1045,360),(1070,415),(1095,462),(1105,500),(1130,550),(1142,600),(1128,650),(1122,668)]),
   ('s', [(1000,312),(1100,314),(1210,312),(1335,306)]),
   ('s', [(1095,462),(1130,445),(1170,435),(1200,440)]),
   ('drip', [(1070,495),(1070,545)]), ('drip', [(1195,520),(1195,605)])],
 'O2': [  # loop counter-clockwise from the top spike, then the tall leaf on its right
   ('s', [(1262,255),(1250,305),(1215,345),(1190,405),(1195,470),(1225,515),(1290,538),(1360,535),(1398,500),(1405,440),(1385,385),(1350,350)]),
   ('s', [(1345,205),(1400,265),(1425,330),(1440,395),(1425,455),(1395,500)])],
 'L': [  # the tall blade down, then the long foot sweeping up and to the right
   ('s', [(1558,100),(1505,150),(1490,215),(1498,285),(1512,350),(1520,420),(1495,490),(1470,540)]),
   ('s', [(1340,608),(1410,572),(1470,542),(1540,540),(1610,538)])],
 'I': [  # the leaf and the blade below it in one stroke, then the leaf's cross-stroke and the lower flick
   ('s', [(1668,152),(1635,228),(1625,300),(1622,350),(1628,405),(1655,455),(1690,520),(1722,556)]),
   ('s', [(1595,232),(1640,240),(1700,248)]),
   ('s', [(1590,392),(1630,405)]),
   ('drip', [(1613,265),(1613,340)]), ('drip', [(1672,552),(1672,640)])],
 'O3': [  # outer loop counter-clockwise from the top, then the inner band
   ('s', [(1830,265),(1760,300),(1705,380),(1710,455),(1755,510),(1830,545),(1920,556),(1990,525),(2022,450),(1998,375),(1940,320),(1880,282),(1830,265)]),
   ('s', [(1852,318),(1812,365),(1808,430),(1840,480),(1900,512),(1960,505),(1995,470)]),
   ('drip', [(1797,548),(1797,630)]), ('drip', [(1968,445),(1968,497)])],
}
ORDER = ['P', 'O', 'R', 'T', 'F', 'O2', 'L', 'I', 'O3']
ZONE = {k: i for i, k in enumerate(ORDER)}

def snap(x, y, rad=70):                                               # nearest strong point of the letter to a waypoint
    cx, cy = int(x / 2), int(y / 2); r = int(rad / 2)
    y0, y1, x0, x1 = max(cy - r, 0), min(cy + r + 1, H2), max(cx - r, 0), min(cx + r + 1, W2)
    win = dt[y0:y1, x0:x1].copy()
    yy, xx = np.mgrid[y0:y1, x0:x1]; win = win - 0.08 * np.hypot(yy - cy, xx - cx)       # prefer thick AND close
    win[~m[y0:y1, x0:x1]] = -1e9
    j = np.unravel_index(np.argmax(win), win.shape); return (y0 + j[0], x0 + j[1])

def route(wps):
    pts = [snap(x, y) for x, y in wps]; path = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        if a == b: continue
        seg, _ = route_through_array(COST, a, b, fully_connected=True, geometric=True); path += [tuple(p) for p in seg[1:]]
    return path

def dehairpin(q):                                                     # cut out places where the route runs out along a spur and straight back
    q = q.copy()
    for _ in range(20):
        n = len(q); found = False
        for k in range(4, n - 4):
            a, b = q[k] - q[k - 4], q[k + 4] - q[k]; na, nb = np.hypot(*a), np.hypot(*b)
            if na < 1e-6 or nb < 1e-6 or np.degrees(np.arccos(np.clip(a @ b / (na * nb), -1, 1))) <= 140: continue
            m = 0
            while k - m - 1 >= 0 and k + m + 1 < n and np.hypot(*(q[k - m - 1] - q[k + m + 1])) < 4.5: m += 1
            if m >= 3: q = np.concatenate([q[:k - m], q[k + m + 1:]]); found = True; break
        if not found: break
    return q

def resample(path, spacing=3.0, rmin=3, sig=2):
    p = np.array(path, float)[:, ::-1]
    if len(p) >= 5: p = np.stack([ndi.gaussian_filter1d(p[:, 0], sig, mode='nearest'), ndi.gaussian_filter1d(p[:, 1], sig, mode='nearest')], 1)
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; L = s[-1]
    if L < 3: return None
    t = np.linspace(0, L, max(2, int(L / spacing) + 1)); q = dehairpin(np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1))
    if len(q) < 3: return None
    r = ndi.gaussian_filter1d(ndi.map_coordinates(dt, [q[:, 1], q[:, 0]], order=1, mode='nearest'), 3, mode='nearest')
    return q, np.maximum(r, rmin)

strokes = []                                                           # (letter index, kind, q, r) in writing order
for k in ORDER:
    for kind, wps in LETTERS[k]:
        if kind == 'drip':
            (x0, y0), (x1, y1) = wps; t = np.linspace(0, 1, max(2, int(np.hypot(x1 - x0, y1 - y0) / 6)))
            q = np.stack([(x0 + (x1 - x0) * t) / 2, (y0 + (y1 - y0) * t) / 2], 1); r = np.full(len(t), 2.6)      # thin and steady
            strokes.append((ZONE[k], 'drip', q, r)); continue
        res = resample(route(wps), sig=3.5)
        if res: strokes.append((ZONE[k], 's', res[0], res[1]))

def paint(S):
    g = np.zeros(m.shape, bool)
    for _, _, q, r in S:
        for (x, y), rr in zip(q, r): yy, xx = disk((y, x), rr * 1.08 + .5, shape=m.shape); g[yy, xx] = True
    return g

cov1 = paint(strokes); left = m & ~cov1
print(f'hand-written strokes: {len(strokes)} | cover {100*(m&cov1).sum()/m.sum():.1f}% of the lettering')
# fill-in: whatever the written strokes missed gets curved follow-the-shape strokes, filed under the letter they belong to (after its main strokes)
from skimage.morphology import skeletonize
CUTS = [40, 400, 640, 840, 1010, 1190, 1360, 1580, 1700, 2030]
K = np.ones((3, 3), int); K[1, 1] = 0
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
def degree(s): return ndi.convolve(s.astype(int), K, mode='constant') * s
def prune(s, k):
    p = s.copy()
    for _ in range(k): p &= ~(degree(p) <= 1)
    for _ in range(k): p |= ndi.binary_dilation(degree(p) == 1, structure=np.ones((3, 3))) & s
    return p
def extract(sk, W, H):
    ep = degree(sk) == 1; vis = np.zeros_like(sk); out = []; hand = None; cols = np.arange(W)[None, :]
    for z in range(9):
        x0 = 0 if z == 0 else CUTS[z] / 2; x1 = 1e9 if z == 8 else CUTS[z + 1] / 2; first = True
        while True:
            ys, xs = np.nonzero(sk & ~vis & (cols >= x0) & (cols < x1))
            if not len(ys): break
            adj = (ndi.binary_dilation(vis, structure=np.ones((3, 3))) & sk & ~vis)[ys, xs]; e = ep[ys, xs]
            grp = np.nonzero(e)[0] if e.any() else (np.nonzero(adj)[0] if (adj.any() and not first) else np.arange(len(ys)))
            if first or hand is None: i = grp[np.argmin(xs[grp] + .35 * ys[grp])]
            else: i = grp[np.argmin((xs[grp] - hand[1]) ** 2 + (ys[grp] - hand[0]) ** 2)]
            first = False; cur = (int(ys[i]), int(xs[i])); path = [cur]; vis[cur] = True
            while True:
                cy, cx = cur
                cand = [(cy + dy, cx + dx) for dy, dx in N8 if 0 <= cy + dy < H and 0 <= cx + dx < W and sk[cy + dy, cx + dx] and not vis[cy + dy, cx + dx]]
                if not cand: break
                ref = path[-6] if len(path) >= 6 else path[0]; dv = (cx - ref[1], cy - ref[0])
                if len(path) < 2 or dv == (0, 0): nxt = cand[0]
                else:
                    def ang(c):
                        v = (c[1] - cx, c[0] - cy); dd = np.hypot(*dv) * np.hypot(*v)
                        return np.degrees(np.arccos(np.clip((dv[0] * v[0] + dv[1] * v[1]) / dd, -1, 1)))
                    nxt = min(cand, key=ang)
                    if ang(nxt) > 110: break
                for c in cand:
                    if c != nxt and max(abs(c[0] - nxt[0]), abs(c[1] - nxt[1])) <= 1: vis[c] = True
                vis[nxt] = True; path.append(nxt); cur = nxt
            if len(path) >= 3: out.append((z, path)); hand = path[-1]
    return out
left = ndi.binary_opening(left, structure=np.ones((3, 3)))
lab, n = ndi.label(left, structure=np.ones((3, 3))); sz = ndi.sum(left, lab, range(1, n + 1)); left = np.isin(lab, [i + 1 for i, s_ in enumerate(sz) if s_ >= 12])
dt2 = ndi.distance_transform_edt(left); touch = []
for z, p in extract(prune(skeletonize(left), 2), W2, H2):
    res = resample(p, 3.5, 3.5)
    if res is None: continue
    q, r = res; rr = ndi.gaussian_filter1d(ndi.map_coordinates(dt2, [q[:, 1], q[:, 0]], order=1, mode='nearest'), 2, mode='nearest')
    if np.hypot(*np.diff(q, axis=0).T).sum() * 2 < 22: continue          # skip specks; the final settle covers them
    touch.append((z, 't', q, np.maximum(rr, 3.5)))
cov2 = cov1 | paint(touch)
print(f'plus {len(touch)} fill-in strokes -> {100*(m&cov2).sum()/m.sum():.1f}%')

allS = []
for z in range(9):
    allS += [s for s in strokes if s[0] == z] + [s for s in touch if s[0] == z]
out = []
for z, kind, q, r in allS:
    pts = []
    for (x, y), rr in zip(q, r): pts += [int(round(x * 2 + 1)), int(round(y * 2 + 1)), int(np.clip(round(rr * 2 * 1.08), 6, 72))]
    out.append({'l': z, 'k': kind, 'p': pts})
json.dump(out, open('/home/claude/strokes_guided.json', 'w'), separators=(',', ':'))
print('total strokes', len(out), '| data KB', round(len(json.dumps(out, separators=(",", ":"))) / 1024, 1))

# preview: strokes over the artwork. brush width drawn; touch-ups in white; numbers show writing order
import colorsys
im = Image.open('/mnt/user-data/uploads/1791523354597_image.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (18, 18, 26, 255)); bg.alpha_composite(im)
bg = Image.blend(bg.convert('RGB'), Image.new('RGB', im.size, (18, 18, 26)), .5); d = ImageDraw.Draw(bg)
for i, o in enumerate(out):
    p = o['p']; c = (255, 255, 255) if o['k'] == 't' else tuple(int(255 * v) for v in colorsys.hsv_to_rgb((o['l'] / 9 + .02) % 1, .9, 1))
    d.line([(p[j], p[j + 1]) for j in range(0, len(p), 3)], fill=c, width=4)
    if o['k'] != 't': d.text((p[0] + 4, p[1] - 12), str(i), fill=(255, 255, 255)); d.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), outline=(255, 255, 255))
bg.save('/home/claude/guided_preview.png')

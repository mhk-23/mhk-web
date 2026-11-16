from PIL import Image
import numpy as np, json
from scipy import ndimage as ndi
im = Image.open('face.png').convert('RGBA'); a = np.array(im); H, W = a.shape[:2]; op = a[..., 3] > 8
rgb = a[..., :3].astype(int); lum = rgb.mean(2); sat = rgb.max(2) - rgb.min(2)
black = op & (lum < 60); skin = op & (rgb[..., 0] > 200) & (sat > 25) & (rgb[..., 0] - rgb[..., 2] > 25); grey = op & (lum > 150) & (sat < 25)
S8 = np.ones((3, 3))
gl, gn = ndi.label(grey, structure=S8); info = []
for i in range(1, gn + 1):
    ys, xs = np.nonzero(gl == i); info.append((i, len(ys), xs.mean(), ys.mean(), xs.min(), xs.max(), ys.min(), ys.max()))
ears = sorted([t for t in info if t[1] > 300 and (t[2] < 170 or t[2] > 400)], key=lambda t: t[2]); assert len(ears) == 2, ears
EL, ER = gl == ears[0][0], gl == ears[1][0]
skinish = skin | (grey & ~EL & ~ER); M = ndi.binary_fill_holes(skinish) & ~EL & ~ER
# label map: 1 hair, 2 face region, 3/4 earrings
L = np.zeros((H, W), np.uint8); L[black] = 1; L[M] = 2; L[EL] = 3; L[ER] = 4
def nearest_fill(L, valid_mask):                                   # give anti-aliased blend pixels the label of their nearest neighbour
    todo = valid_mask & (L == 0); idx = ndi.distance_transform_edt(L == 0, return_distances=False, return_indices=True)
    L2 = L.copy(); L2[todo] = L[idx[0][todo], idx[1][todo]]; return L2
L = nearest_fill(L, op)
# inside the face region: which dark/grey bits are *features* (eyes, brows, nose, lips) vs ear details that stay with the skin
sub = np.zeros((H, W), np.uint8); sub[(L == 2) & skin] = 21
for mask in ((L == 2) & black, (L == 2) & grey):
    cl, cn = ndi.label(mask, structure=S8)
    for i in range(1, cn + 1):
        ys, xs = np.nonzero(cl == i); sub[cl == i] = 22 if 155 <= xs.mean() <= 410 else 23
sub = nearest_fill(sub, L == 2); sub[L != 2] = 0
FEAT = sub == 22
SKINL = (L == 2) & ~FEAT                                           # face skin + ear details
# ---- layers ----
def layer(mask, fill=None):
    out = np.zeros_like(a); out[mask] = a[mask]; return out
hair = np.zeros_like(a); hair[L == 1] = a[L == 1]; hair[(L >= 2)] = [0, 0, 0, 255]                    # solid black under every moving part
skinc = np.array([232, 192, 168, 255], np.uint8)
skin_l = layer(SKINL); skin_l[FEAT] = skinc                                                          # skin carries on beneath the features
feat_l, el_l, er_l = layer(FEAT), layer(L == 3), layer(L == 4)
for n_, arr in (('hair', hair), ('skin', skin_l), ('feat', feat_l), ('earl', el_l), ('earr', er_l)): Image.fromarray(arr).save(f'face_{n_}.png', optimize=True)
# ---- verify: layers stacked at rest must equal the original drawing exactly ----
comp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for n_ in ('hair', 'skin', 'feat', 'earl', 'earr'): comp.alpha_composite(Image.open(f'face_{n_}.png'))
c = np.array(comp).astype(int); o = a.astype(int); d = np.abs(c - o).max(2)
print('layers recombine to the original: pixels that differ =', int((d > 0).sum()), '| largest difference =', int(d.max()), '(of', int(op.sum()), 'drawn px)')
print('pixels per layer: hair', int((L == 1).sum()), '| skin', int(SKINL.sum()), '| features', int(FEAT.sum()), '| earrings', int(EL.sum()), int(ER.sum()))
piv = lambda m: (round(100 * (np.nonzero(m)[1].min() + np.nonzero(m)[1].max()) / 2 / W, 3), round(100 * (np.nonzero(m)[0].min() + 1) / H, 3))
json.dump({'earl': piv(EL), 'earr': piv(ER), 'W': W, 'H': H, 'earl_len': int(np.ptp(np.nonzero(EL)[0]) + 1), 'earr_len': int(np.ptp(np.nonzero(ER)[0]) + 1)}, open('face_layers.json', 'w'))
print('earring pivots (% of canvas):', piv(EL), piv(ER))
# ---- visual check: head turned right / rest / turned left, earrings swinging ----
def frame(s, ear):
    k = 557 / 216; out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bgc = Image.new('RGBA', (W, H), (150, 150, 150, 255)); out = bgc.copy()
    def shift(img, dx): return img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, 0), resample=Image.BICUBIC)
    out.alpha_composite(Image.open('face_hair.png')); out.alpha_composite(shift(Image.open('face_skin.png'), s * .022 * 216 * k)); out.alpha_composite(shift(Image.open('face_feat.png'), s * .05 * 216 * k))
    for n_, key, ang in (('earl', 'earl', ear), ('earr', 'earr', ear * .8)):
        px, py = json.load(open('face_layers.json'))[key]; e = Image.open(f'face_{n_}.png').rotate(-ang, center=(px / 100 * W, py / 100 * H), resample=Image.BICUBIC); out.alpha_composite(e)
    return out.convert('RGB')
sheet = Image.new('RGB', (W * 3, H)); [sheet.paste(frame(s, e), (i * W, 0)) for i, (s, e) in enumerate(((1, 14), (0, 0), (-1, -14)))]; sheet.save('face_turn_check.png')

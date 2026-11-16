from PIL import Image
import numpy as np, glob, os, json
from scipy import ndimage as ndi
from skimage.morphology import disk
files = sorted(glob.glob('/mnt/user-data/uploads/17917907*_image.png') + glob.glob('/mnt/user-data/uploads/17917908*_image.png'), key=os.path.getmtime)
# per piece: working width, 'ink' threshold (brightness above this counts as art), closing radius (bridges texture gaps), fill enclosed black?, edge softness, extra line thickening
P = {
 1:  dict(w=900,  thr=14, r=11, fill=True,  soft=1.2),
 2:  dict(w=900,  thr=6,  r=7,  fill=True,  soft=1.0),
 3:  dict(w=800,  thr=6,  r=6,  fill=True,  soft=1.0),
 4:  dict(w=800,  thr=6,  r=0,  fill=False, soft=.8, thick=2),
 5:  dict(w=900,  thr=14, r=6,  fill=True,  soft=1.2),
 6:  dict(w=1000, thr=6,  r=5,  fill=False, soft=1.0),
 7:  dict(w=800,  thr=6,  r=4,  fill=False, soft=1.0),
 8:  dict(w=1100, thr=60, r=2,  fill=False, soft=.8),
 9:  dict(w=1000, thr=6,  r=5,  fill=False, soft=1.0),
 10: dict(w=1100, thr=14, r=6,  fill=True,  soft=1.2),
}
meta = {}
for i, f in enumerate(files, 1):
    p = P[i]; im = Image.open(f).convert('RGB'); k = p['w'] / im.width if im.width >= im.height else p['w'] / im.height * 1.0
    k = min(1, p['w'] / im.width) if im.width >= im.height else min(1, p['w'] / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS); a = np.array(im); V = a.max(2)
    ink = V > p['thr']
    S = ndi.binary_closing(np.pad(ink, p['r'] + 2), structure=disk(p['r']))[p['r'] + 2:-(p['r'] + 2), p['r'] + 2:-(p['r'] + 2)] if p['r'] > 0 else ink
    if p.get('thick'): S = ndi.binary_dilation(S, structure=disk(p['thick']))
    if p['fill']: S = ndi.binary_fill_holes(S)
    alpha = np.clip(ndi.gaussian_filter(S.astype(float), p['soft']), 0, 1)
    rgba = np.dstack([a, (alpha * 255).astype(np.uint8)]); out = Image.fromarray(rgba, 'RGBA')
    bb = out.getchannel('A').point(lambda v: 255 if v > 12 else 0).getbbox(); pad = 8; bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(out.width, bb[2] + pad), min(out.height, bb[3] + pad)); out = out.crop(bb)
    fn = f'cut/p{i:02d}'; out.save(fn + '.png')
    dark = i in (2, 3, 4, 6, 7, 9)
    out.save(fn + '.webp', 'WEBP', lossless=True, method=6) if dark else out.save(fn + '.webp', 'WEBP', quality=90, method=6)
    meta[i] = {'w': out.width, 'h': out.height, 'kb': os.path.getsize(fn + '.webp') // 1024, 'opaque_%': round(100 * S.mean(), 1)}
print({i: (m['w'], m['h'], str(m['kb']) + 'KB') for i, m in meta.items()}, '| total KB', sum(m['kb'] for m in meta.values()))
json.dump(meta, open('cut/meta.json', 'w'))
# contact sheet over the wall texture
wall = Image.open('wall_l.jpg').convert('RGBA'); sheet = Image.new('RGBA', (1700, 1000)); 
for x in range(0, 1700, wall.width):
    for y in range(0, 1000, wall.height): sheet.paste(wall, (x, y))
pos = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1)]
for i, (cx, cy) in enumerate(pos, 1):
    c = Image.open(f'cut/p{i:02d}.png'); c.thumbnail((330, 470)); sheet.alpha_composite(c, (cx * 340 + (340 - c.width) // 2, cy * 500 + (500 - c.height) // 2))
sheet.convert('RGB').save('cutouts_sheet.png')

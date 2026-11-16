from PIL import Image
import numpy as np, glob, os, json
src = {'team-e': '3E0E9BC1', 'killerx': '33574664', 'lightning': 'A1154CA0'}
W = {'team-e': 1100, 'killerx': 1100, 'lightning': 900}; meta = {}
for name, pre in src.items():
    f = glob.glob(f'/mnt/user-data/uploads/{pre}-*.png')[0]; P = np.array(Image.open(f).convert('RGB')).astype(float); m = P.min(2)
    bgpix = m[m > 225]; floor = np.percentile(bgpix, 3)                         # how white is the paper, really?
    raw = np.clip((255 - m) / 255, 0, 1); t0 = (255 - floor) / 255 + .012       # anything within the paper's own noise counts as background
    alpha = np.clip((raw - t0) / (1 - t0), 0, 1)
    a_raw = np.maximum(raw, 1e-3)[..., None]; C = np.clip((P - 255 * (1 - a_raw)) / a_raw, 0, 255)       # un-mix the ink from the white paper
    out = Image.fromarray(np.dstack([C.astype(np.uint8), (alpha * 255).astype(np.uint8)]), 'RGBA')
    bb = out.getchannel('A').point(lambda v: 255 if v > 10 else 0).getbbox(); pad = 8
    out = out.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(out.width, bb[2] + pad), min(out.height, bb[3] + pad)))
    w = min(W[name], out.width); out = out.resize((w, round(out.height * w / out.width)), Image.LANCZOS)
    out.save(f'letters/{name}.png'); out.save(f'letters/{name}.webp', 'WEBP', quality=94, method=6)
    meta[name] = {'w': out.width, 'h': out.height, 'ar': round(out.width / out.height, 4), 'kb': os.path.getsize(f'letters/{name}.webp') // 1024}
    print(f'{name:10s} paper floor {floor:.0f}/255 -> background threshold {t0:.3f} | opaque {100*(alpha>.97).mean():.1f}% | partly transparent {100*((alpha>.04)&(alpha<=.97)).mean():.1f}% | {meta[name]}')
old = json.load(open('letters/meta.json')); old.update(meta); json.dump(old, open('letters/meta.json', 'w'))
from PIL import Image as I
wall = I.open('wall_l.jpg').convert('RGBA'); sheet = I.new('RGBA', (1750, 560))
for x in range(0, 1750, wall.width):
    for y in range(0, 560, wall.height): sheet.paste(wall, (x, y))
for i, n in enumerate(['team-e', 'killerx', 'lightning']):
    c = I.open(f'letters/{n}.png'); c.thumbnail((560, 500)); sheet.alpha_composite(c, (i * 580 + (580 - c.width) // 2, (560 - c.height) // 2))
sheet.convert('RGB').save('newletters_sheet.png')

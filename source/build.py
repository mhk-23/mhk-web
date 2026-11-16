import re, base64, hashlib, sys
s = open('new_script5.js').read()
js = s.replace('__STROKES__', open('strokes_guided.json').read()); open('check_final.js','w').write(js)
tpl = open('portfolio_tpl.html').read()
tpl = re.sub(r'<script>.*?</script>', lambda m: '<script>\n' + js + '</script>', tpl, flags=re.S); open('portfolio_tpl.html','w').write(tpl)
png = open('/mnt/user-data/uploads/1791523354597_image.png','rb').read()
html = tpl.replace('__ART__', 'data:image/png;base64,' + base64.b64encode(png).decode())
for key, f in (('__WALL_L__', 'wall_l.jpg'), ('__WALL_P__', 'wall_p.jpg')): html = html.replace(key, 'data:image/jpeg;base64,' + base64.b64encode(open(f, 'rb').read()).decode())
from PIL import Image as _I
b64 = lambda f: 'data:image/png;base64,' + base64.b64encode(open(f, 'rb').read()).decode()
for NAME, img_f, sh_f, dims_f in (('CAN', 'can.png', 'can_shadow.png', 'shadow_dims.txt'), ('FACE', 'face.png', 'face_shadow.png', 'shadow_dims_face.txt')):
    _c = _I.open(img_f); _W, _H, _P = map(int, open(dims_f).read().split())
    for k, v in ((f'__{NAME}_AR__', f'{_c.width} / {_c.height}'), (f'__{NAME}_SH_L__', f'{-100*_P/_W:.4f}%'), (f'__{NAME}_SH_T__', f'{-100*_P/_H:.4f}%'), (f'__{NAME}_SH_W__', f'{100*(_W+2*_P)/_W:.4f}%'), (f'__{NAME}_SH_H__', f'{100*(_H+2*_P)/_H:.4f}%'), (f'__{NAME}_SHADOW__', b64(sh_f)), (f'__{NAME}__', b64(img_f))): html = html.replace(k, v)
import json as _j
_fl = _j.load(open('face_layers.json'))
for k, f in (('__FACE_HAIR__', 'face_hair.png'), ('__FACE_SKIN__', 'face_skin.png'), ('__FACE_FEAT__', 'face_feat.png'), ('__FACE_EARL__', 'face_earl.png'), ('__FACE_EARR__', 'face_earr.png')): html = html.replace(k, b64(f))
html = html.replace('__EARL_OX__', f"{_fl['earl'][0]}% {_fl['earl'][1]}%").replace('__EARR_OX__', f"{_fl['earr'][0]}% {_fl['earr'][1]}%")
for _i in range(1, 11): html = html.replace(f'__P{_i:02d}__', 'data:image/webp;base64,' + base64.b64encode(open(f'cut/p{_i:02d}.webp', 'rb').read()).decode())
for _i, _k in enumerate(['tea-party', 'ms-bean', 'appetite', 'slow-state', 'label-jenn', 'team-e', 'killerx', 'lightning'], 1): html = html.replace(f'__L{_i}__', 'data:image/webp;base64,' + base64.b64encode(open(f'letters/{_k}.webp', 'rb').read()).decode())
import re as _r; assert not _r.search(r'__[A-Z0-9_]+__', html), _r.findall(r'__[A-Z0-9_]+__', html)
open('/mnt/user-data/outputs/portfolio-landing.html','w').write(html)
emb = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', html).group(1)
print('PNG identical:', hashlib.md5(base64.b64decode(emb)).hexdigest()==hashlib.md5(png).hexdigest())

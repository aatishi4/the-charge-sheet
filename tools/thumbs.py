#!/usr/bin/env python3
"""
thumbs.py

Makes the smaller images the site serves in place of the originals:
  img/oem/thumb/<name>.webp   catalog and planner cards (at most 600 x 300)
  img/aatish-<w>.webp         the photo on the home page and About, 400, 560 and 800 wide
  img/home/gear/thumb/, img/home/veh/thumb/   home gear cards (cutouts at most 640 x 340; photos cover 560 x 280)

    pip install pillow
    python3 tools/thumbs.py

Run it after adding a charger image. Cards fall back to the full image if a thumb is missing.
"""
import glob, json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fit(im, w, h):
    im = im.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    return im


def main():
    out = os.path.join(ROOT, 'img', 'oem', 'thumb')
    os.makedirs(out, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(ROOT, 'img', 'oem', '*.webp'))):
        im = Image.open(f)
        dest = os.path.join(out, os.path.basename(f))
        fit(im, 600, 300).save(dest, 'WEBP', quality=80, method=6)
        print(os.path.relpath(dest, ROOT), os.path.getsize(dest) // 1024, 'KB')
    photo = Image.open(os.path.join(ROOT, 'img', 'aatish.jpg')).convert('RGB')
    for w in (400, 560, 800):
        dest = os.path.join(ROOT, 'img', 'aatish-%d.webp' % w)
        photo.resize((w, round(photo.height * w / photo.width)), Image.LANCZOS).save(dest, 'WEBP', quality=78, method=6)
        print(os.path.relpath(dest, ROOT), os.path.getsize(dest) // 1024, 'KB')

    gear = json.load(open(os.path.join(ROOT, 'data', 'home-gear.json'), encoding='utf-8'))
    for lst in gear.values():
        for x in (lst if isinstance(lst, list) else []):
            if not (isinstance(x, dict) and x.get('img')):
                continue
            src = os.path.join(ROOT, x['img'])
            dest = os.path.join(os.path.dirname(src), 'thumb', os.path.basename(src))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            im = Image.open(src)
            if x.get('imgFit') == 'photo':  # cards crop photos to fill about 350 x 175, so 560 x 280 covers most screens
                k = min(1, max(560 / im.width, 280 / im.height))
                im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
            else:
                im = fit(im, 640, 340)
            im.save(dest, 'WEBP', quality=80, method=6)
            print(os.path.relpath(dest, ROOT), os.path.getsize(dest) // 1024, 'KB')


if __name__ == '__main__':
    main()

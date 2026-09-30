#!/usr/bin/env python3
"""
thumbs.py

Makes the smaller images the site serves in place of the originals:
  img/oem/thumb/<name>.webp   catalog and planner cards (at most 600 x 300)
  img/aatish-<w>.webp         the photo on the home page and About, 400 and 800 wide

    pip install pillow
    python3 tools/thumbs.py

Run it after adding a charger image. Cards fall back to the full image if a thumb is missing.
"""
import glob, os
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
    for w in (400, 800):
        dest = os.path.join(ROOT, 'img', 'aatish-%d.webp' % w)
        photo.resize((w, round(photo.height * w / photo.width)), Image.LANCZOS).save(dest, 'WEBP', quality=78, method=6)
        print(os.path.relpath(dest, ROOT), os.path.getsize(dest) // 1024, 'KB')


if __name__ == '__main__':
    main()

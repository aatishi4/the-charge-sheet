"""Parts kit for blog art: reusable line-art pieces in the site's style.

Build a post's header art or figure from parts instead of drawing every shape by hand:

    import sys; sys.path.insert(0, 'tools')
    from parts import *
    body = (ground() + pole(60) + wires(60, 700) + transformer(150) +
            charger(300, kind='dc', t=.3) + car(360, motion='drive', t=.6) + cable(330, 96, 372, 112, t=1.4) +
            battery(560, 40, to=.8, frm=.1, t=1.2))
    write('my-slug', body)                  # posts/art/my-slug.svg, viewBox 0 0 720 150
    write('my-figure', hbars([...]), h=None)  # a figure; height fits the content

Conventions:
- x is the left edge of a part and y is the ground line it stands on (default 128 in a 150-high header).
- t is the start delay in seconds. Keep a whole drawing under about 3 seconds.
- Moving parts (drive, bob, fill, rise) put the position on an outer <g transform> and the motion
  class on an inner <g>. A motion class and a transform="" on the same element makes the shape jump to
  the origin while it animates; tools/blog.py refuses to build that.
- Header text is hidden on phones, so a header must read without words. Figure text is 14px in a
  720-wide drawing; keep labels short and let the caption carry the numbers.

Motions (CSS lives in index.html, mirrored in spots.py):
    d       draws a stroke (needs pathLength="1")      fade    fades in
    grow    bar grows up                               growx   bar grows across (from 25%)
    fill    fills across from --from (0 to 1)           filly   fills up from --from
    drive   slides in from --dx (default -160px)       rise    fades in while lifting 10px
    flow    dashes move along a line (loops)           ping    expanding ring (loops)
    bob     gentle up and down (loops)                 count   <text> counts up to its final value

Run `python3 tools/parts.py demo out.html` for a page that shows every part and motion.
"""

import html as _html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def d(t):
    """Delay attribute for a start time in seconds."""
    return ' style="--d:%.2fs"' % t


def _style(**kv):
    kv = {k: v for k, v in kv.items() if v is not None}
    return ' style="%s"' % ';'.join('--%s:%s' % (k, v) for k, v in kv.items()) if kv else ''


def at(x, y, body, motion=None, t=0, **vars_):
    """Place body at (x, y). With a motion, the motion class goes on an inner group (see Conventions)."""
    if motion:
        body = '<g class="%s"%s>%s</g>' % (motion, _style(d='%.2fs' % t, **vars_), body)
    return '<g transform="translate(%g,%g)">%s</g>' % (x, y, body) if (x or y) else body


# ---------- Ground, grid and wires ----------

def ground(y=128, x1=20, x2=700):
    return '<path class="lt" d="M%g,%g H%g"/>' % (x1, y, x2)


def flowline(path, cls='lb'):
    """A light track with moving dashes on top: power or money moving along a path."""
    return '<path class="lt" d="%s"/><path class="%s flow" d="%s"/>' % (path, cls, path)


def pole(x, y=128, t=0, h=96):
    """Wooden utility pole with a crossarm and insulators. x is the pole's center."""
    top = y - h
    return ('<path class="ln d" pathLength="1" d="M%g,%g V%g M%g,%g H%g M%g,%g H%g"%s/>' % (
        x, y, top, x - 22, top + 10, x + 22, x - 14, top + 22, x + 14, d(t)) +
        ''.join('<circle class="ln fw fade" cx="%g" cy="%g" r="3"%s/>' % (x + dx, top + 6, d(t + .6)) for dx in (-18, 0, 18)))


def wires(x1, x2, y=38, sag=10, t=0, n=2):
    """Overhead lines between two poles, with power flowing."""
    return ''.join(flowline('M%g,%g Q%g,%g %g,%g' % (x1, y + i * 8, (x1 + x2) / 2, y + i * 8 + sag, x2, y + i * 8)) for i in range(n))


def transformer(x, y=128, t=0):
    """Pad-mount transformer: the box every charging site waits months for."""
    return ('<rect class="ln d fm" pathLength="1" x="%g" y="%g" width="54" height="40" rx="4"%s/>' % (x, y - 40, d(t)) +
            '<path class="ln fade" d="M%g,%g h18 M%g,%g h18"%s/>' % (x + 8, y - 30, x + 8, y - 24, d(t + .5)) +
            bolt(x + 38, y - 20, 9, t + .7))


def bolt(cx, cy, r=10, t=0, cls='fa'):
    """A lightning bolt centered on (cx, cy), about 2r tall."""
    s = r / 16.0
    pts = [(3, -16), (-10, 3), (-1, 3), (-4, 16), (10, -4), (1, -4)]
    return '<path class="%s fade" d="M%s Z"%s/>' % (cls, ' L'.join('%.1f,%.1f' % (cx + a * s, cy + b * s) for a, b in pts), d(t))


def badge(cx, cy, r=22, t=0, ping=True):
    """Round brand badge with a bolt. Generic on purpose: never draw a real company's logo."""
    return ('<circle class="ln d fw" pathLength="1" cx="%g" cy="%g" r="%g"%s/>' % (cx, cy, r, d(t)) +
            bolt(cx, cy, r * .72, t + .4) +
            ('<circle class="lb ping" cx="%g" cy="%g" r="%g"%s/>' % (cx, cy, r, d(t + .8)) if ping else ''))


# ---------- Chargers, batteries, cables ----------

def charger(x, y=128, t=0, kind='l2', lit=True):
    """A charger standing on the ground. kind: 'l2' (slim post), 'dc' (cabinet with screen and holster)."""
    if kind == 'dc':
        w, h = 34, 64
        out = '<rect class="ln d fw" pathLength="1" x="%g" y="%g" width="%g" height="%g" rx="6"%s/>' % (x, y - h, w, h, d(t))
        out += '<rect class="fi fade" x="%g" y="%g" width="20" height="14" rx="2"%s/>' % (x + 7, y - h + 9, d(t + .5))
        out += '<rect class="ln fade" x="%g" y="%g" width="8" height="12" rx="2"%s/>' % (x + w - 2, y - 38, d(t + .5))
        if lit:
            out += '<circle class="fb fade" cx="%g" cy="%g" r="3"%s/>' % (x + 17, y - h + 34, d(t + .7))
        return out
    out = '<rect class="ln d fw" pathLength="1" x="%g" y="%g" width="14" height="36" rx="3"%s/>' % (x, y - 36, d(t))
    if lit:
        out += '<rect class="fb fade" x="%g" y="%g" width="8" height="8" rx="1.5"%s/>' % (x + 3, y - 30, d(t + .5))
    return out


def cable(x1, y1, x2, y2, t=0, cls='lb'):
    """A charging cable that draws itself from (x1, y1) to (x2, y2), drooping in between."""
    mx, my = (x1 + x2) / 2, max(y1, y2) + 14
    return '<path class="%s d" pathLength="1" d="M%g,%g Q%g,%g %g,%g"%s/>' % (cls, x1, y1, mx, my, x2, y2, d(t))


def battery(x, y, w=120, h=40, to=.8, frm=0.0, t=0, cls='fb', label=True):
    """Battery outline that fills from frm to `to` (0 to 1). With label, the percentage counts up."""
    out = '<rect class="ln fw" x="%g" y="%g" width="%g" height="%g" rx="7"/>' % (x, y, w, h)
    out += '<rect class="ln" x="%g" y="%g" width="7" height="%g" rx="2"/>' % (x + w, y + h * .3, h * .4)
    inner = (w - 10) * to
    out += '<rect class="%s fill" x="%g" y="%g" width="%.1f" height="%g" rx="4"%s/>' % (
        cls, x + 5, y + 5, inner, h - 10, _style(d='%.2fs' % t, **{'from': '%.3f' % (frm / to if to else 0)}))
    if label:
        out += '<text x="%g" y="%g" text-anchor="middle" class="b count" data-from="%d"%s>%d%%</text>' % (
            x + w / 2, y + h + 18, round(frm * 100), d(t), round(to * 100))
    return out


# ---------- Vehicles ----------

_CAR = 'M0,-2 v-12 q0,-6 6,-6 h8 l10,-10 h26 l10,10 h4 q6,0 6,6 v12 z'
_CAR_W = 66


def car(x, y=128, t=0, motion=None, dx=None, flip=False, port=False):
    """A car whose wheels sit on y. x is its left edge (about 66 wide).
    motion: None, 'drive' (rolls in from dx, default -160px), 'bob' (idles), or 'rise'.
    flip=True faces it left. port=True marks the charge port (rear corner, about x+5, y-12) in blue."""
    body = ('<path class="ln d fw" pathLength="1" d="%s"%s/>' % (_CAR, d(t)) +
            '<circle class="ln fw" cx="14" cy="-2" r="5"/><circle class="ln fw" cx="54" cy="-2" r="5"/>')
    if port:
        body += '<circle class="fb" cx="5" cy="-12" r="2.5"/>'
    if flip:
        body = '<g transform="matrix(-1,0,0,1,%d,0)">%s</g>' % (_CAR_W, body)
    extra = {'dx': '%dpx' % dx} if (motion == 'drive' and dx is not None) else {}
    return at(x, y, body, motion, t, **extra)


def truck(x, y=128, t=0, motion=None, dx=None, trailer=True):
    """A semi: tractor plus box trailer, about 190 wide with the trailer. x is the left edge."""
    body = ''
    if trailer:
        body += '<rect class="ln d fw" pathLength="1" x="0" y="-62" width="128" height="52" rx="3"%s/>' % d(t)
        body += '<circle class="ln fw" cx="20" cy="-4" r="6"/><circle class="ln fw" cx="36" cy="-4" r="6"/>'
    ox = 132 if trailer else 0
    body += ('<path class="ln d fw" pathLength="1" d="M%d,-10 V-50 q0,-6 6,-6 h26 l14,20 h6 q4,0 4,4 v22 z"%s/>' % (ox, d(t + .2)) +
             '<rect class="fi" x="%d" y="-50" width="18" height="12" rx="2"/>' % (ox + 8) +
             '<circle class="ln fw" cx="%d" cy="-4" r="6"/><circle class="ln fw" cx="%d" cy="-4" r="6"/>' % (ox + 12, ox + 46))
    extra = {'dx': '%dpx' % dx} if (motion == 'drive' and dx is not None) else {}
    return at(x, y, body, motion, t, **extra)


# ---------- Buildings ----------

def store(x, y=128, t=0, w=52):
    """A small shop or c-store with a door."""
    return ('<path class="ln d fw" pathLength="1" d="M%g,%g V%g L%g,%g L%g,%g V%g Z"%s/>' % (
        x, y, y - 44, x + w / 2, y - 58, x + w, y - 44, y, d(t)) +
        '<rect class="fi fade" x="%g" y="%g" width="16" height="28" rx="2"%s/>' % (x + w / 2 - 8, y - 28, d(t + .5)))


def hotel(x, y=128, t=0, floors=4, w=96):
    """A hotel: a block with rows of windows, the lights coming on floor by floor."""
    fh = 18
    h = floors * fh + 16
    out = '<rect class="ln d fw" pathLength="1" x="%g" y="%g" width="%g" height="%g" rx="3"%s/>' % (x, y - h, w, h, d(t))
    for f in range(floors):
        for c in range(4):
            out += '<rect class="fas fade" x="%g" y="%g" width="12" height="9" rx="1.5"%s/>' % (
                x + 10 + c * (w - 32) / 3, y - 26 - f * fh, d(t + .4 + f * .12))
    out += '<rect class="fi fade" x="%g" y="%g" width="18" height="14" rx="2"%s/>' % (x + w / 2 - 9, y - 14, d(t + .4))
    return out


def house(x, y=128, t=0, w=70):
    """A house with a garage door (for the home side)."""
    return ('<path class="ln d fw" pathLength="1" d="M%g,%g V%g L%g,%g L%g,%g V%g Z"%s/>' % (
        x, y, y - 40, x + w / 2, y - 66, x + w, y - 40, y, d(t)) +
        '<path class="lt fade" d="M%g,%g h30 M%g,%g h30 M%g,%g h30"%s/>' % (
            x + 8, y - 22, x + 8, y - 14, x + 8, y - 6, d(t + .5)) +
        '<rect class="fi fade" x="%g" y="%g" width="16" height="14" rx="2"%s/>' % (x + w - 26, y - 34, d(t + .5)))


def depot(x, y=128, t=0, w=200, bays=3):
    """A fleet depot: a long low shed with bay doors."""
    out = '<path class="ln d fw" pathLength="1" d="M%g,%g V%g L%g,%g H%g L%g,%g V%g Z"%s/>' % (
        x, y, y - 50, x + 20, y - 66, x + w - 20, x + w, y - 50, y, d(t))
    bw = (w - 20 * (bays + 1)) / bays
    for i in range(bays):
        out += '<rect class="fm fade" x="%g" y="%g" width="%g" height="34" rx="2"%s/>' % (x + 20 + i * (bw + 20), y - 34, bw, d(t + .4 + i * .1))
    return out


def gas_pump(x, y=128, t=0):
    """A 1910s-1920s visible gas pump: glass cylinder on a tall column. For history pieces."""
    return ('<path class="ln d fw" pathLength="1" d="M%g,%g V%g H%g V%g Z"%s/>' % (x + 6, y, y - 60, x + 26, y, d(t)) +
            '<rect class="ln d fi" pathLength="1" x="%g" y="%g" width="32" height="34" rx="6"%s/>' % (x, y - 96, d(t + .2)) +
            '<path class="la fade" d="M%g,%g h24 M%g,%g h24 M%g,%g h24"%s/>' % (
                x + 4, y - 86, x + 4, y - 76, x + 4, y - 66, d(t + .6)) +
            '<circle class="ln fw fade" cx="%g" cy="%g" r="7"%s/>' % (x + 16, y - 104, d(t + .7)) +
            '<path class="ln d" pathLength="1" d="M%g,%g c14,0 18,14 12,28"%s/>' % (x + 26, y - 50, d(t + .8)))


# ---------- Labels and figure helpers ----------

def label(x, y, text, cls='', anchor=None, t=None, count=False, frm=None, dur=None):
    """Text. count=True makes the number in it count up when the drawing plays (the final value stays
    in the markup for screen readers, no-JS and reduced motion)."""
    classes = ' '.join(c for c in [cls, 'count' if count else '', 'fade' if t is not None else ''] if c)
    attrs = ' text-anchor="%s"' % anchor if anchor else ''
    if classes:
        attrs += ' class="%s"' % classes
    if count and frm is not None:
        attrs += ' data-from="%s"' % frm
    if count and dur is not None:
        attrs += ' data-dur="%s"' % dur
    return '<text x="%g" y="%g"%s%s>%s</text>' % (x, y, attrs, d(t) if t is not None else '', _html.escape(text))


def hbars(rows, x=20, width=560, top=40, gap=58, maxv=None, footer=None, t0=0.1, step=.25):
    """Horizontal bar figure. rows: dicts with label, value, and optional shown (text after the bar,
    defaults to the value), color ('fs' grey, 'fb' blue, 'fa' amber), and count (default True).
    Returns SVG body; pass h=None to write() to size it."""
    maxv = maxv or max(r['value'] for r in rows)
    out, y = [], top
    for i, r in enumerate(rows):
        fill = r.get('color', 'fs')
        tc = {'fb': 'b', 'fa': 'a'}.get(fill, '')
        t = t0 + i * step
        w = width * r['value'] / maxv
        out.append(label(x, y - 8, r['label'], tc))
        out.append('<rect class="lt" x="%g" y="%g" width="%g" height="22" rx="5"/>' % (x, y, width))
        out.append('<rect class="%s growx" x="%g" y="%g" width="%.0f" height="22" rx="5"%s/>' % (fill, x, y, w, d(t)))
        shown = r.get('shown', str(r['value']))
        out.append(label(min(x + w + 10, x + width + 14), y + 17, shown, tc, t=t + .2, count=r.get('count', True),
                         dur=1.8))
        y += gap
    if footer:
        out.append('<path class="lt dash" d="M%g,%g H%g"/>' % (x, y - 16, x + width))
        out.append(label(x, y + 12, footer, t=t0 + len(rows) * step + .6))
        y += 20
    return '\n'.join(out)


def svg(body, h=150):
    if h is None:
        ys = [float(v) for v in re.findall(r'\by="(-?[\d.]+)"', body)]
        h = int(max(ys or [130]) + 16)
    return '<svg viewBox="0 0 720 %d" focusable="false">\n%s\n</svg>\n' % (h, body)


def write(name, body, h=150):
    """Write posts/art/<name>.svg. h=None sizes the drawing to its content (for figures)."""
    if not re.match(r'^[a-z0-9-]+$', name):
        raise SystemExit('parts: art names are lowercase letters, digits and hyphens')
    path = os.path.join(ROOT, 'posts', 'art', name + '.svg')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg(body, h))
    return path


# ---------- Demo page ----------

def _demo_scenes():
    return [
        ('Drive in, plug in, fill up', 'drive, d, fill and count together: the scene most posts need.',
         ground() + pole(50) + transformer(110) + flowline('M72,40 C110,40 130,70 137,88') + flowline('M164,110 H250') + charger(250, kind='dc', t=.2) +
         car(300, t=.5, motion='drive', port=True) + cable(286, 92, 305, 116, t=1.7) +
         battery(470, 48, w=150, to=.8, frm=.1, t=1.9), 150),
        ('Every part', 'charger (l2, dc), car, truck, store, hotel, house, depot, gas pump, pole, transformer, badge.',
         ground() + badge(40, 40, t=0) + pole(100) + transformer(120, t=.1) + charger(190, t=.2) + charger(212, kind='dc', t=.3) +
         store(262, t=.4) + hotel(326, t=.5) + house(436, t=.6) + gas_pump(520, t=.7) + depot(566, w=134, bays=2, t=.8), 150),
        ('Vehicles in motion', 'car with drive and with bob; truck with drive (dx sets how far it travels).',
         ground() + car(40, t=.1, motion='drive') + car(170, t=.3, motion='bob', flip=True) +
         truck(300, t=.2, motion='drive', dx=-260) + charger(530, kind='dc', t=.3) + charger(574, kind='dc', t=.4) +
         flowline('M564,40 H700'), 150),
        ('Step-by-step reveal', 'rise with staggered delays: grid, transformer, charger, car, in order.',
         ground() + at(0, 0, pole(70), 'rise', 0) + at(0, 0, transformer(150), 'rise', .5) +
         at(0, 0, charger(300, kind='dc'), 'rise', 1.0) + at(0, 0, car(360, port=True), 'rise', 1.5) + cable(336, 92, 365, 116, t=2.0) +
         flowline('M92,40 C140,40 160,80 176,88') + flowline('M204,108 H300') +
         label(70, 146, '1. Grid', anchor='middle', t=.1) + label(176, 146, '2. Transformer', anchor='middle', t=.6) +
         label(317, 146, '3. Charger', anchor='middle', t=1.1) + label(393, 146, '4. Car', anchor='middle', t=1.6), 150),
        ('Figure: bars with count-up', 'hbars(): growx bars with numbers that count up as the bars grow.',
         hbars([{'label': 'Net new stalls, Q3 2025', 'value': 100},
                {'label': 'Net new stalls, Q3 2026', 'value': 59, 'shown': '59 (-41%)', 'color': 'fa'},
                {'label': 'Sessions, Q3 2025', 'value': 100},
                {'label': 'Sessions, Q3 2026', 'value': 129, 'shown': '129 (+29%)', 'color': 'fb'}],
               footer='Index, Q3 2025 = 100. Example data.'), None),
        ('Vertical fill', 'filly: a bar that fills up from --from, with a count-up label.',
         ''.join('<rect class="lt" x="%d" y="20" width="60" height="100" rx="6"/>'
                 '<rect class="%s filly" x="%d" y="%d" width="60" height="%d" rx="6"%s/>' % (
                     80 + i * 140, c, 80 + i * 140, 120 - v, v, _style(d='%.2fs' % (.2 + i * .3)))
                 + label(110 + i * 140, 140, '%d%%' % v, {'fb': 'b', 'fa': 'a'}.get(c, ''), 'middle', t=.2 + i * .3, count=True)
                 for i, (v, c) in enumerate([(16, 'fs'), (34, 'fa'), (72, 'fb'), (95, 'fb')])), 150),
    ]


def demo(out_path, standalone=True):
    """Write a page showing every part and motion, with replay buttons, in the site's colors."""
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    roots = re.findall(r'(:root\{[^}]*--white[^}]*\})', src)[:1]
    dark = re.search(r'@media \(prefers-color-scheme: ?dark\)\{\s*:root(?::not\(\[data-theme="light"\]\))?\{([^}]*--white[^}]*)\}', src)
    css = re.search(r'/\* ---------- Header illustrations ---------- \*/(.*?)@media print\{\.spot\{display:none\}\}', src, re.S).group(1)
    js = re.search(r'(function spotCounts\(root\)\{.*?\n  \})\n', src, re.S).group(1)
    scenes = ''.join(
        '<section><h2>%s</h2><p>%s</p><div class="spot io">%s</div><button type="button">Replay</button></section>' % (
            _html.escape(tt), _html.escape(sub), svg(body, h).strip()) for tt, sub, body, h in _demo_scenes())
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Charge Sheet art kit</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&display=swap">
<style>
%s
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){%s}}
:root[data-theme="dark"]{%s}
body{margin:0;background:var(--white);color:var(--ink);font:16px/1.5 "Instrument Sans",system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding-block:24px 64px;padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px))}
h1,h2{text-wrap:balance}
button:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
h1{font-size:1.6rem;margin:.2rem 0} h2{font-size:1.05rem;margin:2.2rem 0 .1rem} p{margin:.2rem 0;color:var(--slate)}
section{border-top:1px solid var(--line);margin-top:1.4rem}
button{margin-top:.4rem;font:inherit;font-size:.85rem;padding:.3rem .8rem;border-radius:8px;border:1px solid var(--line);background:var(--mist);color:var(--ink);cursor:pointer}
.bar{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
%s
.js .spot.io:not(.play) *{animation-play-state:paused}
@media (max-width:640px){.spot text{display:none}}
</style></head><body><main>
<h1>Charge Sheet art kit</h1>
<p>Every part and motion in tools/parts.py, drawn with the site's own CSS. Each drawing plays on load and again when you scroll to it. Replay runs it once more.</p>
<div class="bar"><button type="button" id="theme">Switch light or dark</button><button type="button" id="all">Replay all</button></div>
%s
</main><script>
var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
document.documentElement.classList.add('js');
%s
function replay(s){ s.classList.remove('play'); s.querySelectorAll('.count').forEach(function(c){ c.removeAttribute('data-done'); });
  var svg = s.querySelector('svg'); var copy = svg.cloneNode(true); svg.replaceWith(copy); void s.offsetWidth; s.classList.add('play'); spotCounts(s); }
document.querySelectorAll('section').forEach(function(sec){ var s = sec.querySelector('.spot');
  sec.querySelector('button').addEventListener('click', function(){ replay(s); }); });
document.getElementById('all').addEventListener('click', function(){ document.querySelectorAll('.spot').forEach(replay); });
document.getElementById('theme').addEventListener('click', function(){ var r = document.documentElement;
  var dk = r.getAttribute('data-theme') === 'dark' || (!r.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
  r.setAttribute('data-theme', dk ? 'light' : 'dark'); });
document.querySelectorAll('.spot').forEach(function(s){ s.classList.add('play'); spotCounts(s); });
var io2 = ('IntersectionObserver' in window && !REDUCED) ? new IntersectionObserver(function(es){ es.forEach(function(e){
  if (e.isIntersecting){ replay(e.target); io2.unobserve(e.target); } }); }, {threshold:.35}) : null;
if (io2) document.querySelectorAll('.spot').forEach(function(s){ if (s.getBoundingClientRect().top > innerHeight) io2.observe(s); });
</script></body></html>
''' % (roots[0] if roots else '', dark.group(1) if dark else '', dark.group(1) if dark else '', css, scenes, js)
    if not standalone:
        page = re.sub(r'^<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport"[^>]*>\n?|</head><body>|</body></html>\s*$', '', page)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(page)
    return out_path


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == 'demo':
        print(demo(sys.argv[2] if len(sys.argv) > 2 else 'art-kit.html'))
    else:
        print(__doc__)

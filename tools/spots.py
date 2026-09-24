"""Header illustrations for the guides and the blog. One-off source: add_spots() writes them into index.html."""

CSS = '''
/* ---------- Header illustrations ---------- */
.spot{margin:1.8rem 0 .4rem;max-width:720px}
.spot svg{display:block;width:100%;height:auto;overflow:visible}
.spot .ln{fill:none;stroke:var(--ink);stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.spot .lt{fill:none;stroke:var(--line);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.spot .lb{fill:none;stroke:var(--blue);stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.spot .la{fill:none;stroke:var(--amber);stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.spot .dash{stroke-dasharray:4 6}
.spot .fm{fill:var(--mist)}
.spot .fw{fill:var(--white)}
.spot .fi{fill:var(--ice)}
.spot .fb{fill:var(--blue)}
.spot .fa{fill:var(--amber)}
.spot .fas{fill:var(--amber-soft)}
.spot .fs{fill:var(--line)}
.spot text{font:600 11px/1 "Instrument Sans",system-ui,sans-serif;fill:var(--slate);letter-spacing:.02em}
.spot text.b{fill:var(--blue)} .spot text.a{fill:var(--amber)}
.spot .d{stroke-dasharray:1;stroke-dashoffset:1;animation:spotdraw 1.3s cubic-bezier(.3,.6,.2,1) forwards;animation-delay:var(--d,0s)}
.spot .fade{opacity:0;animation:spotfade .6s ease forwards;animation-delay:var(--d,0s)}
.spot .grow{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:spotgrow .9s cubic-bezier(.3,.6,.2,1) forwards;animation-delay:var(--d,0s)}
.spot .growx{transform-box:fill-box;transform-origin:0 50%;transform:scaleX(.25);animation:spotgrowx 2.4s cubic-bezier(.4,.1,.2,1) forwards;animation-delay:var(--d,0s)}
.spot .flow{stroke-dasharray:3 13;animation:spotflow 1.4s linear infinite}
.spot .ping{transform-box:fill-box;transform-origin:center;animation:spotping 2.4s ease-out infinite;animation-delay:var(--d,0s)}
.spot .bob{animation:spotbob 3s ease-in-out infinite}
@keyframes spotdraw{to{stroke-dashoffset:0}}
@keyframes spotfade{to{opacity:1}}
@keyframes spotgrow{to{transform:scaleY(1)}}
@keyframes spotgrowx{to{transform:scaleX(1)}}
@keyframes spotflow{to{stroke-dashoffset:-32}}
@keyframes spotping{0%{transform:scale(.6);opacity:.9}100%{transform:scale(1.9);opacity:0}}
@keyframes spotbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
@media (prefers-reduced-motion: reduce){
  .spot .d{animation:none;stroke-dashoffset:0}
  .spot .fade{animation:none;opacity:1}
  .spot .grow,.spot .growx{animation:none;transform:none}
  .spot .flow,.spot .ping,.spot .bob{animation:none}
  .spot .ping{opacity:0}
}
@media print{.spot{display:none}}
@media (max-width:640px){.spot{margin-top:1.2rem}.spot text{display:none}}
'''


def svg(body, h=150):
    return ('<div class="spot" aria-hidden="true"><svg viewBox="0 0 720 %d" focusable="false">%s</svg></div>' % (h, body))


def d(delay):
    return ' style="--d:%.2fs"' % delay


# 1. How EV charging works: grid, AC wave, charger, DC line, battery filling
def _sine(x0, y, n, w, a):
    s = 'M%d,%d ' % (x0, y)
    s += 'q%.2f,%d %.2f,0 ' % (w / 2, -a, w)
    s += ' '.join('t%.2f,0' % w for _ in range(n - 1))
    return s


BASICS = svg(
    # tower
    '<path class="ln d" pathLength="1" d="M52,132 L70,30 L88,132 M40,44 H100 M46,62 H94 M58,96 H82 M62,74 L80,120 M78,74 L60,120"%s/>' % d(0) +
    '<text x="70" y="148" text-anchor="middle">Grid</text>' +
    # AC wave
    '<path class="lt" d="%s"/><path class="lb flow" d="%s"/>' % (_sine(108, 84, 8, 19, 16), _sine(108, 84, 8, 19, 16)) +
    '<text x="184" y="120" text-anchor="middle" class="b">AC</text>' +
    # charger
    '<rect class="ln d fw" pathLength="1" x="262" y="34" width="62" height="100" rx="12"%s/>' % d(.25) +
    '<rect class="fi fade" x="275" y="48" width="36" height="22" rx="4"%s/><circle class="fb fade" cx="293" cy="92" r="4"%s/>' % (d(.8), d(.9)) +
    '<text x="293" y="148" text-anchor="middle">Charger</text>' +
    # DC line
    '<path class="lt" d="M324,84 H452"/><path class="lb flow" d="M324,84 H452"/>' +
    '<text x="388" y="120" text-anchor="middle" class="b">DC</text>' +
    # battery
    '<rect class="ln d" pathLength="1" x="456" y="56" width="178" height="56" rx="10"%s/>' % d(.45) +
    '<rect class="ln" x="634" y="72" width="10" height="24" rx="3"/>' +
    '<rect class="fb growx" x="464" y="64" width="138" height="40" rx="5"%s/>' % d(1.1) +
    '<path class="lt" d="M607,62 V106" stroke-dasharray="3 4"/><text x="607" y="54" text-anchor="middle">80%</text>' +
    '<text x="545" y="148" text-anchor="middle">Battery</text>'
)

# 2. The business: a bill and a month of power draw with one spike
_bars = [14, 18, 12, 22, 16, 20, 11, 15, 24, 19, 13, 17, 21, 14, 18, 16, 96, 20, 15, 12, 19, 23, 14, 17, 13, 21, 16, 18, 12, 15]
BUSINESS = svg(
    '<path class="ln d fw" pathLength="1" d="M40,18 H176 V124 l-11.33,8 -11.33,-8 -11.33,8 -11.33,-8 -11.33,8 -11.33,-8 -11.33,8 -11.33,-8 -11.33,8 -11.33,-8 -11.33,8 -11.33,-8 V18 Z"%s/>' % d(0) +
    '<path class="lt" d="M58,44 H130 M58,62 H112 M58,80 H124"/>' +
    '<path class="la" d="M58,100 H100"/><text x="158" y="104" text-anchor="end" class="a">$$$</text>' +
    '<path class="lt" d="M214,132 H700"/>' +
    ''.join('<rect class="%s grow" x="%d" y="%d" width="10" height="%d" rx="2"%s/>' % (
        'fa' if h > 50 else 'fb', 222 + i * 16, 132 - h, h, d(.3 + i * .025)) for i, h in enumerate(_bars)) +
    '<path class="la dash fade" d="M214,36 H700"%s/>' % d(1.4) +
    '<text x="700" y="28" text-anchor="end" class="a fade"%s>One busy afternoon sets the whole month</text>' % d(1.6) +
    '<text x="214" y="148">Power drawn each day of the month</text>'
)

# 3. Real estate: a street grid, four identical chargers, one good address
REALESTATE = svg(
    '<rect class="fm" x="10" y="8" width="700" height="134" rx="14"/>' +
    '<path class="lt" d="M10,52 H710 M10,104 H710 M130,8 V142 M300,8 V142 M470,8 V142 M620,8 V142"/>' +
    '<path class="lt" d="M10,78 H710" style="stroke-width:7"/>' +
    ''.join(
        '<g class="fade"%s><path class="%s" d="M%d,%d c0,-14 -12,-16 -12,-26 a12,12 0 1 1 24,0 c0,10 -12,12 -12,26 z"/>'
        '<circle class="fw" cx="%d" cy="%d" r="4.5"/></g>' % (d(.2 + i * .2), cls, x, y, x, y - 26)
        for i, (x, y, cls) in enumerate([(215, 70, 'fs'), (385, 124, 'fs'), (545, 44, 'fb'), (80, 122, 'fs')])) +
    '<circle class="lb ping" cx="545" cy="18" r="16"%s/>' % d(1.2) +
    '<text x="560" y="36" class="b fade"%s>Same box, busier address</text>' % d(1.3)
)

# 4. Paying for it: cash, grants, a loan, and the balance going down
FINANCE = svg(
    '<path class="ln d" pathLength="1" d="M40,56 L90,30 L140,56 Z M46,62 H134 M54,66 V108 M72,66 V108 M90,66 V108 M108,66 V108 M126,66 V108 M42,114 H138"%s/>' % d(0) +
    '<text x="90" y="138" text-anchor="middle">Loan</text>' +
    '<path class="lt" d="M190,120 H560 M190,20 V120"/>' +
    '<path class="lb d" pathLength="1" d="M196,30 C270,34 330,52 390,74 S500,112 556,118"%s/>' % d(.4) +
    '<text x="196" y="138">Balance, year by year</text>' +
    ''.join('<ellipse class="fade %s" cx="640" cy="%d" rx="34" ry="9"%s/>' % ('fas' if i % 2 else 'fi', 118 - i * 12, d(.8 + i * .12)) for i in range(7)) +
    '<ellipse class="la fade" cx="640" cy="46" rx="34" ry="9"%s/>' % d(1.7) +
    '<text x="640" y="138" text-anchor="middle">Cash and grants</text>'
)

# 5. Batteries: a load curve clipped at the grid limit, battery covers the peak
_curve = 'M40,124 C110,122 150,112 200,96 C250,80 280,30 340,28 C400,26 430,82 480,98 C540,116 600,122 680,124'
STORAGE = svg(
    '<defs><clipPath id="spot-peak"><rect x="0" y="0" width="720" height="62"/></clipPath></defs>' +
    '<path class="fi" d="%s V130 H40 Z"/>' % _curve +
    '<path class="fas grow" d="%s V130 H40 Z" clip-path="url(#spot-peak)"%s/>' % (_curve, d(1.2)) +
    '<path class="lb d" pathLength="1" d="%s"%s/>' % (_curve, d(0)) +
    '<path class="la dash" d="M30,62 H690"/><text x="690" y="54" text-anchor="end" class="a">Grid limit</text>' +
    '<text x="340" y="20" text-anchor="middle" class="a fade"%s>The battery covers this part</text>' % d(1.5) +
    '<path class="lt" d="M30,130 H690"/><text x="40" y="148">Midnight</text><text x="680" y="148" text-anchor="end">Midnight</text>' +
    '<g class="bob"><rect class="ln fw" x="560" y="10" width="60" height="30" rx="6"/><rect class="ln" x="620" y="18" width="6" height="14" rx="2"/>'
    '<rect class="fa" x="566" y="16" width="30" height="18" rx="3"/></g>'
)

# 6. Connectivity: tower, signal, charger, server
CONNECT = svg(
    '<path class="ln d" pathLength="1" d="M70,134 L86,48 L102,134 M78,92 H94 M74,114 H98"%s/>' % d(0) +
    '<circle class="fb" cx="86" cy="42" r="5"/>' +
    ''.join('<path class="lb ping" d="M%d,%d a%d,%d 0 0 1 0,%d" style="--d:%.1fs"/>' % (100, 42 - r, r, r, 2 * r, i * .8) for i, r in enumerate([14, 14, 14])) +
    '<text x="86" y="150" text-anchor="middle">Carrier</text>' +
    '<path class="lt" d="M120,70 C220,70 260,96 330,96"/><path class="lb flow" d="M120,70 C220,70 260,96 330,96"/>' +
    '<rect class="ln d fw" pathLength="1" x="334" y="44" width="58" height="92" rx="11"%s/>' % d(.3) +
    '<rect class="fi" x="346" y="58" width="34" height="20" rx="4"/><circle class="fb" cx="363" cy="98" r="4"/>' +
    '<text x="363" y="150" text-anchor="middle">Charger</text>' +
    '<path class="lt" d="M392,70 C470,70 500,40 560,40"/><path class="lb flow" d="M392,70 C470,70 500,40 560,40" style="animation-direction:reverse"/>' +
    '<path class="ln d fw" pathLength="1" d="M570,58 h86 a18,18 0 0 0 -2,-36 a24,24 0 0 0 -44,-6 a18,18 0 0 0 -40,18 a13,13 0 0 0 0,24 z"%s/>' % d(.6) +
    '<text x="614" y="80" text-anchor="middle">Back office</text>' +
    '<path class="la dash" d="M540,112 H690"/><text x="615" y="130" text-anchor="middle" class="a">Payments, authorization, pricing</text>'
)

# 7. Buying: the six layers, stacked, with one that needs a hard look
_layers = ['Service', 'Installation', 'Hardware', 'Payments', 'Software', 'Your brand']
VENDORS = svg(
    ''.join(
        '<g class="fade"%s><path class="%s" d="M%d,%d l90,-14 l90,14 l-90,14 z" style="stroke:var(--ink);stroke-width:1.6;stroke-linejoin:round"/><text x="%d" y="%d">%s</text></g>' % (
            d(.1 + i * .15), 'fi' if i != 3 else 'fas', 60, 128 - i * 18, 250, 132 - i * 18, name)
        for i, name in enumerate(_layers)) +
    ''.join('<rect class="ln fw" x="420" y="%d" width="18" height="18" rx="4"/><path class="lt" d="M452,%d H%d"/>' % (
        22 + i * 24, 31 + i * 24, 600 - (i % 3) * 40) for i in range(5)) +
    ''.join('<path class="lb d" pathLength="1" d="M424,%d l5,5 l8,-10"%s/>' % (31 + i * 24, d(.9 + i * .2)) for i in (0, 1, 2, 4)) +
    '<path class="la d" pathLength="1" d="M424,%d l10,10 M434,%d l-10,10"%s/>' % (98, 98, d(1.5)) +
    '<text x="420" y="148">Questions to ask, by vendor</text>'
)

# 8. Fleet: vans at chargers, charging to the 80% line
_fill = [(.9, 80), (1.1, 80), (1.3, 58), (1.5, 80)]
FLEET = svg(
    '<path class="la dash" d="M30,40 H690"/><text x="30" y="26" class="a">80%, then the next van</text>' +
    ''.join(
        '<rect class="fm" x="%d" y="30" width="34" height="100" rx="6"/>'
        '<rect class="fb grow" x="%d" y="%d" width="34" height="%d" rx="6"%s/>'
        '<path class="ln" d="M%d,130 H%d"/>'
        '<path class="ln d fw" pathLength="1" d="M%d,130 V96 q0,-10 10,-10 h54 q10,0 18,12 l14,14 q6,4 6,12 v6 z"%s/>'
        '<circle class="ln fw" cx="%d" cy="132" r="8"/><circle class="ln fw" cx="%d" cy="132" r="8"/>' % (
            60 + i * 170, 60 + i * 170, 130 - int(f * 1.12), int(f * 1.12), d(t),
            56 + i * 170, 190 + i * 170,
            100 + i * 170, d(.1 + i * .1),
            122 + i * 170, 176 + i * 170)
        for i, (t, f) in enumerate(_fill)) +
    '<text x="30" y="150">Throughput beats a full battery</text>'
)

# 9. Benchmarks: the spread between best and worst sites
_pts = [5.2, 1.43, 1.38, 1.35, 1.24, 1.07, .54, .35, .34, .23, .12]
BENCH = svg(
    '<path class="lt" d="M40,120 H690"/>' +
    ''.join('<text x="%.0f" y="140" text-anchor="middle">%s</text>' % (40 + 650 * (__import__('math').log10(v / .1) / __import__('math').log10(60)), t)
            for v, t in [(.1, '0.1'), (.3, '0.3'), (1, '1'), (3, '3'), (6, '6')]) +
    ''.join('<circle class="%s fade" cx="%.1f" cy="%d" r="%d"%s/>' % (
        'fb' if v > 5 else 'fs' if v < .3 else 'fi', 40 + 650 * (__import__('math').log10(v / .1) / __import__('math').log10(60)),
        96 - (k % 3) * 22, 9 if v > 5 else 7, d(.1 + k * .08)) for k, v in enumerate(_pts)) +
    '<path class="lb d" pathLength="1" d="M69,40 H688"%s/>' % d(1.2) +
    '<path class="lb" d="M69,34 V46 M688,34 V46"/>' +
    '<text x="378" y="30" text-anchor="middle" class="b fade"%s>About 40 to 1, best site to worst</text>' % d(1.6) +
    '<text x="40" y="20">Sessions per port per day, real sites</text>'
)

# Blog: a notebook and the week's clippings
BLOG = svg(
    '<rect class="ln d fw" pathLength="1" x="40" y="14" width="200" height="124" rx="10"%s/>' % d(0) +
    '<path class="lt" d="M64,40 H216 M64,60 H200 M64,80 H210 M64,100 H170"/>' +
    '<path class="lb d" pathLength="1" d="M64,120 C90,108 110,128 140,114 S190,110 214,118"%s/>' % d(.6) +
    ''.join('<g class="fade"%s><rect class="ln fw" x="%d" y="%d" width="120" height="84" rx="8" transform="rotate(%d %d %d)"/>'
            '<path class="lt" d="M%d,%d h84 M%d,%d h64 M%d,%d h74" transform="rotate(%d %d %d)"/></g>' % (
                d(.3 + i * .2), x, y, r, x + 60, y + 42, x + 18, y + 24, x + 18, y + 42, x + 18, y + 60, r, x + 60, y + 42)
            for i, (x, y, r) in enumerate([(300, 30, -5), (440, 22, 4), (578, 34, -3)])) +
    '<rect class="fa fade" x="468" y="36" width="48" height="10" rx="3" transform="rotate(4 500 64)"%s/>' % d(1.1) +
    '<text x="300" y="146">This week, the three or four things that matter</text>'
)

SPOTS = {'basics': BASICS, 'primer': BUSINESS, 'realestate': REALESTATE, 'finance': FINANCE, 'storage': STORAGE,
         'connectivity': CONNECT, 'vendors': VENDORS, 'fleet': FLEET, 'benchmarks': BENCH}

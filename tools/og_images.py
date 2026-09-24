#!/usr/bin/env python3
"""
og_images.py

Draws the 1200x630 link-preview image for every page into ./og, in the site's
own font and colors. Run it after changing a page's headline below:

    pip install playwright && python -m playwright install chromium
    python3 tools/og_images.py

The build picks up og/<slug>.png automatically. Home uses og-image.png (render_home, with the photo).
"""
import base64, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from build_pages import PAGES  # noqa: E402

# slug: (kicker, headline). Short enough for three lines at preview size.
CARDS = {
    'how-ev-charging-works': ('Guide', 'How charging works, and why sessions fail.'),
    'ev-charging-business-model': ('Guide', 'Is a charging station actually a good business?'),
    'ev-charging-site-selection': ('Guide', "Same charger. Different address. Different business."),
    'ev-charging-station-financing': ('Guide', 'Paying for a charging site: cash, grants, or a loan.'),
    'battery-storage-ev-charging': ('Guide', 'Batteries fix power problems, not energy problems.'),
    'ev-charger-connectivity': ('Guide', 'Most broken chargers are network problems.'),
    'buying-ev-chargers': ('Guide', 'Buying chargers without getting burned.'),
    'fleet-ev-charging': ('Guide', 'Fleet charging is a logistics business.'),
    'ev-charging-benchmarks': ('Data', 'What real charging sites actually do.'),
    'methodology': ('Method', 'Every formula, written out. Change any of them.'),
    'ev-charging-site-planner': ('Free tool', 'Will this charging site make money?'),
    'ev-charger-installation-cost': ('Free tool', 'The charger is the cheap part.'),
    'sba-loan-calculator-ev-charging': ('Free tool', 'Does an SBA loan pencil for this site?'),
    'fleet-charging-calculator': ('Free tool', 'How many vehicles can your depot charge?'),
    'ev-charging-utilization-forecast': ('Free tool', 'How busy will this site be?'),
    'ev-charger-cellular-signal-check': ('Free tool', 'Will this charger stay online?'),
    'ev-charging-glossary': ('Reference', 'Demand charges, OCPP, DSCR, and the rest of the jargon.'),
    'about': ('About', 'Written by someone who learned it the expensive way.'),
}

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:IS;src:url(data:font/woff2;base64,%(font)s) format("woff2");font-weight:400 700;font-stretch:75%% 100%%}
*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;font-family:IS,sans-serif;background:#fff;color:#0D1F36;position:relative;overflow:hidden}
.top{height:420px;padding:64px 72px 0}
.brand{display:flex;align-items:center;gap:14px;font-weight:700;font-size:30px;letter-spacing:-.01em}
.mark{width:40px;height:40px}
.kick{margin-top:30px;font-size:22px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#2462F5}
h1{margin-top:10px;width:630px;font-size:60px;line-height:1.06;letter-spacing:-.025em;font-weight:700}
.band{position:absolute;left:0;right:0;bottom:0;height:210px;background:#F3F7FB;padding:44px 72px 0;font-size:27px;line-height:1.42;color:#5A6B80}
.band span{display:block;max-width:1056px}
.art{position:absolute;right:0;top:168px;width:440px;height:243px}
</style></head><body>
<div class="top">
  <div class="brand"><svg class="mark" viewBox="0 0 24 24"><rect width="24" height="24" rx="7" fill="#2462F5"/><path d="M4.5 12.5q1.6-3 3.2 0t3.2 0L14 12.5h5.5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>The Charge Sheet</div>
  <div class="kick">%(kicker)s</div>
  <h1>%(headline)s</h1>
</div>
<svg class="art" viewBox="0 0 470 260" fill="none" stroke="#0D1F36" stroke-width="2.4">
  <rect x="62" y="36" width="90" height="164" rx="12" fill="#fff"/>
  <rect x="80" y="58" width="54" height="36" rx="5" fill="#E7EFFE" stroke="none"/>
  <circle cx="107" cy="124" r="5" fill="#2462F5" stroke="none"/>
  <path d="M107 200 C 110 240, 170 236, 250 222 S 330 200, 360 180" stroke-width="2.6"/>
  <path d="M107 200 C 110 240, 170 236, 250 222 S 330 200, 360 180" stroke="#2462F5" stroke-dasharray="3 14" stroke-width="2.6"/>
  <path d="M360 150 C 380 140, 420 118, 470 110 L470 188 L358 188 Z" fill="#fff"/>
  <circle cx="392" cy="190" r="17" fill="#fff"/>
  <rect x="300" y="6" width="130" height="42" rx="8" fill="#F3F7FB" stroke="#DCE5EF" stroke-width="1.5"/>
  <rect x="306" y="12" width="102" height="30" rx="5" fill="#2462F5" stroke="none"/>
  <text x="357" y="33" text-anchor="middle" fill="#fff" stroke="none" font-family="IS" font-weight="700" font-size="17">85%%</text>
</svg>
<div class="band"><span>%(desc)s</span></div>
</body></html>"""


def render(page, font, kicker, headline, desc, path):
    esc = lambda t: t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    page.set_content(TEMPLATE % {'font': font, 'kicker': esc(kicker), 'headline': esc(headline), 'desc': esc(desc)})
    page.wait_for_timeout(150)
    page.screenshot(path=path)
    print(os.path.relpath(path, ROOT))


HOME_BAND = ('<div class="band hb"><img src="data:image/jpeg;base64,%(photo)s" alt="">'
             '<span><b>Built by Aatish Patel</b>, founder of XCharge North America. Free guides, real data and '
             'planning tools for the business of EV charging.</span></div>')
HOME_CSS = ('.hb{display:flex;align-items:center;gap:30px;padding-top:0}'
            '.hb img{width:128px;height:128px;border-radius:50%%;object-fit:cover;flex:none;border:4px solid #fff}'
            '.hb b{color:#0D1F36}.hb span{max-width:860px}</style>')


def render_home(page, font, path):
    """Home card (og-image.png): the site headline plus who built it, with a photo."""
    photo = base64.b64encode(open(os.path.join(ROOT, 'img', 'aatish-square.jpg'), 'rb').read()).decode()
    html = TEMPLATE.replace('</style>', HOME_CSS).replace('<div class="band"><span>%(desc)s</span></div>', HOME_BAND)
    html = html.replace('<div class="kick">%(kicker)s</div>', '')
    page.set_content(html % {'font': font, 'kicker': '', 'headline': 'Charging stations look simple. Then the electric bill arrives.', 'desc': '', 'photo': photo})
    page.wait_for_timeout(200)
    page.screenshot(path=path)
    print(os.path.relpath(path, ROOT))


def main():
    """python3 tools/og_images.py            pages, the blog card, and any post missing a card
       python3 tools/og_images.py SLUG ...   just those pages or posts (post slugs without the date); 'home' for og-image.png"""
    from playwright.sync_api import sync_playwright
    import blog
    font = base64.b64encode(open(os.path.join(ROOT, 'fonts', 'InstrumentSans-VF.woff2'), 'rb').read()).decode()
    out = os.path.join(ROOT, 'og')
    os.makedirs(out, exist_ok=True)
    only = set(sys.argv[1:])
    os.environ.setdefault('SHOW_DRAFTS', '1')
    posts = blog.load_posts(ROOT)
    with sync_playwright() as p:
        exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
        browser = p.chromium.launch(executable_path=exe) if exe and os.path.isfile(exe) else p.chromium.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 630})
        for v, slug, title, desc, kind in PAGES:
            if not slug or (only and slug not in only) or slug not in CARDS:
                continue
            kicker, headline = CARDS[slug]
            render(page, font, kicker, headline, desc, os.path.join(out, slug + '.png'))
        if not only or 'home' in only:
            render_home(page, font, os.path.join(ROOT, 'og-image.png'))
        if not only or 'blog' in only:
            render(page, font, 'Blog', 'Notes from the business of EV charging.',
                   'What is changing, what it costs, and what I would do about it. Plus a weekly screen of the news that matters.',
                   os.path.join(out, 'blog.png'))
        for post in posts:
            path = os.path.join(out, 'blog-%s.png' % post['slug'])
            if (only and post['slug'] not in only) or (not only and os.path.exists(path)):
                continue
            kicker = 'The week in charging' if post['kind'] == 'weekly' else 'Blog'
            render(page, font, kicker, post['title'], post['description'], path)
        browser.close()


if __name__ == '__main__':
    main()

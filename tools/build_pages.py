#!/usr/bin/env python3
"""
build_pages.py

Turns the single-file site (index.html) into one real page per guide and tool,
so each has its own URL, title, description, preview image and structured data.

    python3 tools/build_pages.py            # writes ./dist

Cloudflare Pages runs this on every push (build command "python3 tools/build_pages.py",
output directory "dist"). index.html stays the source of truth and still works on its
own when opened directly, using #hash navigation. Standard library only.

How it works, briefly:
  - CSS and JS move into content-hashed files under /assets, cached for a year.
  - Each page gets the site chrome, its own section in full, and every other section
    "hollowed": prose removed, but every element the script hooks into (ids, data-*
    attributes, form controls, SVG) kept, so the shared script runs unchanged.
    Search engines see one page's content per URL.
  - Links between sections become real links between pages.

To add a page: add a <section id="view-NAME"> to index.html, add NAME to VIEWS
in the script, and add a row to PAGES below.
"""
import datetime, hashlib, html, json, os, re, shutil, subprocess
from html.parser import HTMLParser
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog  # noqa: E402
import spots  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
OUT = os.path.join(ROOT, 'dist')
SITE = 'https://chargesheet.io'
SITE_NAME = 'The Charge Sheet'
AUTHOR = {
    '@type': 'Person', 'name': 'Aatish Patel', 'url': SITE + '/about/',
    'image': SITE + '/img/aatish-square.jpg',
    'sameAs': ['https://www.linkedin.com/in/aatish-patel-2b9424a4/', 'https://github.com/aatishi4'],
}
PUBLISHED = '2026-09-24'

# view id, URL slug ('' is home), page title, meta description, kind
PAGES = [
    ('home', '', 'The Charge Sheet: The Business of EV Charging, Explained',
     'A free, honest guide to how EV charging works, what a charging site really costs, and whether it pays. Real benchmark data and free planning tools.', 'home'),
    ('basics', 'how-ev-charging-works', 'How EV Charging Works: AC, DC, and Why Sessions Fail',
     'AC vs DC charging, the charger and car handshake, and why sessions fail, explained for site owners. Enough engineering to follow the money.', 'guide'),
    ('primer', 'ev-charging-business-model', 'Is an EV Charging Station Profitable? The Business Model',
     'Where charging revenue comes from, where it goes, and why demand charges quietly kill sites. Costs, incentives, ownership models, and how sites fail.', 'guide'),
    ('realestate', 'ev-charging-site-selection', "EV Charging Site Selection: It's a Real Estate Business",
     'Two identical fast chargers at four addresses, with very different returns. How to pick, control, and underwrite a charging site like a real estate development.', 'guide'),
    ('finance', 'ev-charging-station-financing', 'How to Finance an EV Charging Station: Cash, Grants, SBA',
     'Three ways to pay for a charging site: business cash flow, public programs, or a loan. What each costs, who it suits, and an SBA lender checklist.', 'guide'),
    ('storage', 'battery-storage-ev-charging', 'Battery Storage for EV Charging: When It Pays',
     "What a battery fixes at a charging site (peak power, demand charges, a smaller service) and what it can't. Sizing, earnings, the 48E credit, and FEOC rules.", 'guide'),
    ('connectivity', 'ev-charger-connectivity', 'EV Charger Connectivity: Why Chargers Go Offline',
     'Most "broken charger" complaints are network problems. What depends on connectivity, cellular vs wired, why the IoT provider matters, and what to do offline.', 'guide'),
    ('vendors', 'buying-ev-chargers', 'Buying EV Chargers: Vendor Questions and Red Flags',
     'What to ask charger vendors, installers, and software providers, what a good answer sounds like, and the walk-away signs. For site hosts and operators.', 'guide'),
    ('fleet', 'fleet-ev-charging', 'Fleet EV Charging: Throughput, Power, and Operations',
     'Fleet charging is a logistics problem. How to plan for throughput, the 80% rule, site power, charge windows, and the operations that make or break a depot.', 'guide'),
    ('benchmarks', 'ev-charging-benchmarks', 'EV Charging Benchmarks: Real Utilization Data',
     'Sessions per day, energy per session, and utilization from operating US charging sites. Session-level data, anonymized, with nothing modeled or rounded up.', 'guide'),
    ('method', 'methodology', 'Method and Sources: How The Charge Sheet Works',
     'Every formula behind the forecast, site planner, and battery math, where the benchmark data comes from, and the limits of each.', 'guide'),
    ('glossary', 'ev-charging-glossary', 'EV Charging Glossary: Terms Every Site Owner Should Know',
     'Demand charges, ratchets, make-ready, OCPP, DSCR, FEOC and the rest of the jargon of EV charging, explained in plain English for people planning and running sites.', 'glossary'),
    ('planner', 'ev-charging-site-planner', 'EV Charging Station Pro Forma and ROI Calculator',
     'Free pro forma for a charging site: build cost, operating cost, NPV, payback, and break-even sessions per day. DC fast and Level 2. Export to a spreadsheet.', 'tool'),
    ('install', 'ev-charger-installation-cost', 'EV Charger Installation Cost Estimator: DC and Level 2',
     'Estimate charger installation cost from distance to the electrical room, trenching, boring, wire, and conduit, and see how fast it grows with placement.', 'tool'),
    ('sbatool', 'sba-loan-calculator-ev-charging', 'SBA Loan Calculator for EV Charging Stations',
     'See whether an SBA 7(a) or 504 loan pencils for a charging project: loan size, monthly payment, and debt service coverage the way a lender will look at it.', 'tool'),
    ('fleettool', 'fleet-charging-calculator', 'Fleet Charging Calculator: Vehicles Per Day',
     "How many vehicles your depot can charge in a day, and what's limiting it: chargers, power, or the people moving cars. Find the bottleneck.", 'tool'),
    ('forecast', 'ev-charging-utilization-forecast', 'EV Charging Utilization Forecast: Sessions Per Day',
     'Forecast sessions per day for a charging site from road traffic or people on site and local EV share. Pulls state DOT traffic counts and nearby station counts.', 'tool'),
    ('sitecheck', 'ev-charger-cellular-signal-check', 'EV Charger Cellular Signal Check: RSRP, RSRQ, SINR',
     'Grade the cellular signal where a charger will stand using RSRP, RSRQ, and SINR readings from AT&T, T-Mobile, and Verizon, and get a setup that holds up.', 'tool'),
    ('about', 'about', 'About The Charge Sheet and Aatish Patel',
     'Who wrote The Charge Sheet and why: lessons from building an EV charging company, written down so you can skip learning them the expensive way.', 'about'),
]
VIEWS = [p[0] for p in PAGES]
PATH = {p[0]: ('/' + p[1] + '/' if p[1] else '/') for p in PAGES}


def last_updated():
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs'], cwd=ROOT, capture_output=True, text=True, timeout=10)
        d = out.stdout.strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            return d
    except Exception:
        pass
    return datetime.date.today().isoformat()


# ---------- a tiny tree that round-trips raw HTML ----------
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
# Elements kept whole, words and all, inside hollowed sections.
HOOK_TAGS = {'select', 'option', 'optgroup', 'datalist', 'textarea', 'button', 'svg', 'canvas',
             'output', 'template', 'script', 'style'}


class Node:
    __slots__ = ('tag', 'raw', 'attrs', 'children', 'closed', 'text')

    def __init__(self, tag=None, raw='', attrs=None, text=None):
        self.tag, self.raw, self.attrs, self.children, self.closed, self.text = tag, raw, attrs or {}, [], False, text

    def html(self):
        if self.text is not None:
            return self.text
        inner = ''.join(c.html() for c in self.children)
        if self.tag is None:
            return inner
        if self.tag in VOID or self.raw.rstrip().endswith('/>'):
            return self.raw + inner
        name = re.match(r'<\s*([^\s/>]+)', self.raw).group(1)
        return self.raw + inner + ('</%s>' % name if self.closed else '')


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, self.get_starttag_text(), dict(attrs))
        self.stack[-1].children.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, self.get_starttag_text(), dict(attrs)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack[i].closed = True
                del self.stack[i:]
                return
        self.stack[-1].children.append(Node(text='</%s>' % tag))

    def handle_data(self, d): self.stack[-1].children.append(Node(text=d))
    def handle_entityref(self, n): self.stack[-1].children.append(Node(text='&%s;' % n))
    def handle_charref(self, n): self.stack[-1].children.append(Node(text='&#%s;' % n))
    def handle_comment(self, d): pass
    def handle_decl(self, d): self.stack[-1].children.append(Node(text='<!%s>' % d))


def parse(fragment):
    t = Tree()
    t.feed(fragment)
    t.close()
    return t.root


def hollow(n):
    """Strip the words, keep the skeleton. Every element stays, so the script finds
    whatever it looks for; text goes, except inside controls and drawings."""
    if n.tag in HOOK_TAGS:
        return
    n.children = [c for c in n.children if c.text is None and 'spot' not in (c.attrs.get('class') or '').split()]
    if n.tag == 'img' and 'alt' in n.attrs:
        n.raw = re.sub(r'\salt="[^"]*"', ' alt=""', n.raw)
    for c in n.children:
        hollow(c)


def hollow_html(fragment):
    root = parse(fragment)
    root.children = [c for c in root.children if c.text is None]
    for c in root.children:
        hollow(c)
    return root.html()


# ---------- helpers ----------
def esc(s):
    return html.escape(s, quote=True)


def absolutize_html(s):
    return re.sub(r'((?:href|src|srcset|poster)=")(?:\./)?((?:fonts|img|data|og)/[^"]*|favicon[^"]*|apple-touch-icon\.png|og-image\.png)"', r'\1/\2"', s)


def absolutize_css(s):
    return re.sub(r'url\((["\']?)(?:\./)?(?!data:|https?:|/|#)', r'url(\1/', s)


def absolutize_js(s):
    return re.sub(r'([\'"])(?:\./)?(img|data|fonts|og)/', r'\1/\2/', s)


def hashed(name, ext, content):
    h = hashlib.sha1(content.encode('utf-8')).hexdigest()[:10]
    return 'assets/%s.%s.%s' % (name, h, ext)


def section_bounds(s):
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="view-([a-z]+)"', s)]
    main_end = s.index('</main>')
    return [(v, pos, starts[i + 1][0] if i + 1 < len(starts) else main_end) for i, (pos, v) in enumerate(starts)]


def rewrite_links(doc, page, anchors):
    def fix(m):
        ident, _, rest = m.group(2).partition('?')
        if ident in PATH:
            return m.group(1) + PATH[ident] + ('?' + rest if rest else '') + '"'
        v = anchors.get(ident)
        if v and v != page:
            return m.group(1) + PATH[v] + '#' + ident + '"'
        return m.group(0)
    return re.sub(r'(href=")#([^"]*)"', fix, doc)


def set_meta(head, title, desc, url, image, kind):
    def sub(pattern, repl):
        nonlocal head
        new, n = re.subn(pattern, lambda m: repl, head, count=1)
        assert n == 1, pattern
        head = new
    sub(r'<title>.*?</title>', '<title>%s</title>' % esc(title))
    sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % esc(desc))
    sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % esc(title))
    sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % esc(desc))
    sub(r'<meta property="og:type" content="[^"]*">', '<meta property="og:type" content="%s">' % ('website' if kind in ('home', 'tool', 'about', 'glossary') else 'article'))
    sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url)
    sub(r'<meta property="og:image" content="[^"]*">', '<meta property="og:image" content="%s">\n<meta property="og:image:alt" content="%s">' % (image, esc(title)))
    sub(r'<meta name="twitter:image" content="[^"]*">', '<meta name="twitter:image" content="%s">\n<meta name="twitter:title" content="%s">\n<meta name="twitter:description" content="%s">' % (image, esc(title), esc(desc)))
    sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">\n<meta name="robots" content="index, follow, max-image-preview:large">' % url)
    return head


GLOSSARY = []


def jsonld(title, desc, url, image, kind, h1, updated):
    graph = []
    author_ref = {'@id': SITE + '/#author'}
    if kind == 'home':
        graph.append({'@type': 'WebSite', '@id': SITE + '/#website', 'name': SITE_NAME, 'url': SITE + '/',
                      'description': desc, 'inLanguage': 'en-US', 'publisher': author_ref})
        graph.append(dict(AUTHOR, **{'@id': SITE + '/#author'}))
    elif kind == 'about':
        graph.append({'@type': 'ProfilePage', 'url': url, 'name': title, 'dateModified': updated,
                      'mainEntity': dict(AUTHOR, **{'@id': SITE + '/#author'})})
    elif kind == 'glossary':
        graph.append({'@type': 'DefinedTermSet', '@id': url + '#terms', 'name': h1 or title, 'url': url, 'description': desc,
                      'hasDefinedTerm': [{'@type': 'DefinedTerm', 'name': t, 'description': dd, 'url': url + '#g-' + gid}
                                         for gid, t, dd in (GLOSSARY or [])]})
    elif kind == 'tool':
        graph.append({'@type': 'WebApplication', 'name': h1 or title, 'url': url, 'description': desc,
                      'applicationCategory': 'BusinessApplication', 'operatingSystem': 'Any', 'isAccessibleForFree': True,
                      'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
                      'author': dict(AUTHOR), 'image': image})
    else:
        graph.append({'@type': 'Article', 'headline': title, 'name': h1 or title, 'description': desc, 'url': url,
                      'mainEntityOfPage': url, 'image': image, 'inLanguage': 'en-US',
                      'datePublished': PUBLISHED, 'dateModified': updated,
                      'author': dict(AUTHOR), 'publisher': dict(AUTHOR),
                      'isPartOf': {'@type': 'WebSite', 'name': SITE_NAME, 'url': SITE + '/'}})
    if kind != 'home':
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': SITE_NAME, 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': h1 or title, 'item': url}]})
    data = {'@context': 'https://schema.org', '@graph': graph}
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(data, ensure_ascii=False).replace('</', '<\\/')


def config_script(page, anchors):
    return '<script>window.CS_PAGE=%s;window.CS_PATHS=%s;window.CS_ANCHORS=%s;</script>\n' % (
        json.dumps(page), json.dumps(PATH), json.dumps(anchors))


BLOG_TITLE = 'Blog: The Charge Sheet'
BLOG_DESC = 'Notes from the business of EV charging: what is changing, what it costs, and what I would do about it. Plus a weekly screen of the news that matters.'


def post_item(p):
    kind = 'The week in charging' if p['kind'] == 'weekly' else '%d min read' % p['minutes']
    badge = ' <span class="badge-draft">Draft</span>' if p['draft'] else ''
    return ('<li><a href="/blog/%s/"><span class="pl-meta"><time datetime="%s">%s</time><br>%s</span>'
            '<b>%s%s</b><span class="pl-d">%s</span></a></li>') % (
        p['slug'], p['date'], blog.nice_date(p['date']), esc(kind), esc(p['title']), badge, esc(p['description']))


def blog_latest_html(posts):
    live = [p for p in posts if not p['draft']][:3] or posts[:3]
    if not live:
        return ''
    return ('<div class="band mist blog-latest"><div class="wrap"><h2>From the blog.</h2>'
            '<p class="lead">What is changing in charging, and what I would do about it.</p>'
            '<ul class="post-list">%s</ul><p style="margin-top:2rem"><a class="btn" href="/blog/">All posts</a></p></div></div>\n') % ''.join(post_item(p) for p in live)


def page_doc(head, pre_main, post_main, hollow_all, anchors, page_id, section, nav_current=None):
    pm = pre_main
    if nav_current:
        pm = pm.replace('id="%s"' % nav_current, 'id="%s" aria-current="true"' % nav_current, 1)
    doc = head + pm + section + hollow_all + post_main
    return rewrite_links(doc, page_id, anchors).replace('%%CS_CONFIG%%', config_script(page_id, anchors))


def build_blog(posts, head, pre_main, post_main, hollow_all, anchors, updated):
    urls = []
    og_default = SITE + ('/og/blog.png' if os.path.exists(os.path.join(ROOT, 'og', 'blog.png')) else '/og-image.png')
    os.makedirs(os.path.join(OUT, 'blog'), exist_ok=True)

    # index
    url = SITE + '/blog/'
    items = ''.join(post_item(p) for p in posts)
    body = ('<section id="view-blog" class="read blog"><div class="tool-head"><h1>Blog</h1>'
            '<p>Notes from the business of EV charging: what is changing, what it costs, and what I would do about it. '
            'Plus a weekly screen of the news that actually matters to people who own or plan charging sites.</p></div>'
            '%s<div class="prose">%s<p class="feed-link"><a href="/blog/feed.xml">Subscribe with RSS</a></p></div></section>\n') % (
        BLOG_ART, '<ul class="post-list">%s</ul>' % items if items else '<p class="blog-empty">The first posts are on the way.</p>')
    h = set_meta(head, BLOG_TITLE, BLOG_DESC, url, og_default, 'home')
    ld = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'The Charge Sheet blog', 'url': url, 'description': BLOG_DESC,
          'author': dict(AUTHOR), 'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': SITE + '/blog/%s/' % p['slug'],
                                                'datePublished': p['date']} for p in posts if not p['draft']]}
    h += '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    h += '<link rel="alternate" type="application/rss+xml" title="The Charge Sheet blog" href="%s/blog/feed.xml">\n' % SITE
    open(os.path.join(OUT, 'blog', 'index.html'), 'w', encoding='utf-8').write(
        page_doc(h, pre_main, post_main, hollow_all, anchors, 'blog', body, 'gn-blog'))
    urls.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, posts[0]['date'] if posts else updated))

    # posts
    for i, p in enumerate(posts):
        url = SITE + '/blog/%s/' % p['slug']
        img = p['image'] if p['image'].startswith('http') else (SITE + p['image'] if p['image'] else '')
        if not img:
            img = SITE + '/og/blog-%s.png' % p['slug'] if os.path.exists(os.path.join(ROOT, 'og', 'blog-%s.png' % p['slug'])) else og_default
        h = set_meta(head, p['title'] + ': The Charge Sheet', p['description'] or BLOG_DESC, url, img, 'guide')
        if p['draft']:
            h = h.replace('content="index, follow, max-image-preview:large"', 'content="noindex"')
        ld = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': p['title'], 'description': p['description'],
              'url': url, 'mainEntityOfPage': url, 'image': img, 'datePublished': p['date'], 'dateModified': p['updated'],
              'inLanguage': 'en-US', 'author': dict(AUTHOR), 'publisher': dict(AUTHOR), 'keywords': ', '.join(p['tags']),
              'isPartOf': {'@type': 'Blog', 'name': 'The Charge Sheet blog', 'url': SITE + '/blog/'}}
        h += '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
        h += '<meta property="article:published_time" content="%s">\n' % p['date']
        h += '<link rel="alternate" type="application/rss+xml" title="The Charge Sheet blog" href="%s/blog/feed.xml">\n' % SITE
        kind = 'The week in charging' if p['kind'] == 'weekly' else '%d min read' % p['minutes']
        tags = '<ul class="tags">%s</ul>' % ''.join('<li>%s</li>' % esc(t) for t in p['tags']) if p['tags'] else ''
        others = [q for q in posts if q is not p and (not q['draft'] or p['draft'])][:3]
        more = ('<h2>More from the blog</h2><ul class="post-list">%s</ul>' % ''.join(post_item(q) for q in others)) if others else ''
        body = ('<section id="view-blogpost" class="read blog"><div class="tool-head">'
                '<p class="post-kicker"><a href="/blog/">Blog</a><span class="dot">/</span><time datetime="%s">%s</time>'
                '<span class="dot">/</span><span>%s</span>%s</p><h1>%s</h1>%s%s</div>'
                '<article class="prose post">%s</article>'
                '<div class="prose post-foot"><div class="post-author"><img src="/img/aatish-square.jpg" alt="" width="56" height="56">'
                '<p><b>Aatish Patel</b><br>Built and ran a charging company for six years. <a href="/about/">More about me</a>.</p></div>%s'
                '<p class="feed-link"><a href="/blog/">All posts</a> <span class="dot">/</span> <a href="/blog/feed.xml">RSS</a></p></div></section>\n') % (
            p['date'], blog.nice_date(p['date']), esc(kind), ' <span class="badge-draft">Draft</span>' if p['draft'] else '',
            esc(p['title']), '<p>%s</p>' % esc(p['description']) if p['description'] else '', tags, p['html'], more)
        d = os.path.join(OUT, 'blog', p['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
            page_doc(h, pre_main, post_main, hollow_all, anchors, 'blog', body, 'gn-blog'))
        if not p['draft']:
            urls.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, p['updated']))

    # RSS
    def rfc822(iso):
        return datetime.datetime.combine(datetime.date.fromisoformat(iso), datetime.time(12)).strftime('%a, %d %b %Y %H:%M:%S +0000')
    items = ''.join(
        '<item><title>%s</title><link>%s/blog/%s/</link><guid isPermaLink="true">%s/blog/%s/</guid><pubDate>%s</pubDate>'
        '<description>%s</description><content:encoded><![CDATA[%s]]></content:encoded>%s</item>' % (
            esc(p['title']), SITE, p['slug'], SITE, p['slug'], rfc822(p['date']), esc(p['description']),
            p['html'].replace(']]>', ']]&gt;').replace('href="/', 'href="%s/' % SITE).replace('src="/', 'src="%s/' % SITE),
            ''.join('<category>%s</category>' % esc(t) for t in p['tags']))
        for p in posts if not p['draft'])
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" '
            'xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><title>The Charge Sheet blog</title>'
            '<link>%s/blog/</link><description>%s</description><language>en-us</language>'
            '<atom:link href="%s/blog/feed.xml" rel="self" type="application/rss+xml"/>%s</channel></rss>\n') % (
        SITE, esc(BLOG_DESC), SITE, items)
    open(os.path.join(OUT, 'blog', 'feed.xml'), 'w', encoding='utf-8').write(feed)
    print('Blog: %d posts (%d drafts).' % (len(posts), sum(1 for p in posts if p['draft'])))
    return urls


BLOG_ART = spots.BLOG


def build():
    src = open(SRC, encoding='utf-8').read()
    updated = last_updated()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'assets'))

    # CSS and JS out to cached files
    styles = re.findall(r'<style>(.*?)</style>', src, re.S)
    scripts = re.findall(r'<script>(.*?)</script>', src, re.S)
    assert len(scripts) == 1, 'expected exactly one inline <script> in index.html'
    css = absolutize_css('\n'.join(styles))
    js = absolutize_js(scripts[0])
    css_path, js_path = hashed('site', 'css', css), hashed('site', 'js', js)
    open(os.path.join(OUT, css_path), 'w', encoding='utf-8').write(css)
    open(os.path.join(OUT, js_path), 'w', encoding='utf-8').write(js)
    state = {'first': True}

    def style_repl(m):
        if state['first']:
            state['first'] = False
            return '<link rel="stylesheet" href="/%s">' % css_path
        return ''
    src = re.sub(r'<style>.*?</style>', style_repl, src, flags=re.S)
    src = re.sub(r'<script>.*?</script>', lambda m: '%%CS_CONFIG%%' + '<script src="/' + js_path + '"></script>', src, flags=re.S)
    src = absolutize_html(src)
    month = datetime.date.fromisoformat(updated).strftime('%B %Y')
    src = re.sub(r'Last updated [A-Z][a-z]+ \d{4}\.', 'Last updated %s.' % month, src)

    # sections, anchors, h1s
    bounds = section_bounds(src)
    missing = set(VIEWS) - set(b[0] for b in bounds)
    assert not missing, 'in PAGES but not in index.html: %s' % missing
    anchors, h1s, full, hollowed = {}, {}, {}, {}
    for v, a, b in bounds:
        frag = src[a:b]
        for ident in re.findall(r'\bid="([^"]+)"', frag):
            if ident != 'view-' + v:
                anchors.setdefault(ident, v)
        if v == 'glossary':
            for gid, dt, dd in re.findall(r'<dt id="g-([^"]+)">(.*?)</dt><dd>(.*?)</dd>', frag, re.S):
                GLOSSARY.append((gid, html.unescape(re.sub(r'<[^>]+>', '', dt)), html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'\s*<a [^>]*>.*?</a>\.?', '', dd))).strip()))
        m = re.search(r'<h1[^>]*>(.*?)</h1>', frag, re.S)
        h1s[v] = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
    for v, a, b in bounds:
        frag = src[a:b]
        full[v] = re.sub(r'(<section id="view-%s"[^>]*?)\s+hidden(?=[\s>])' % v, r'\1', frag, count=1)
        h = hollow_html(frag)
        if not re.match(r'<section id="view-%s"[^>]*\bhidden\b' % v, h):
            h = h.replace('<section id="view-%s"' % v, '<section id="view-%s" hidden' % v, 1)
        hollowed[v] = h + '\n'
    head_end = src.index('</head>')
    head, pre_main = src[:head_end], src[head_end:bounds[0][1]]
    post_main = src[bounds[-1][2]:]

    posts = blog.load_posts(ROOT)
    full['home'] = full['home'].replace('<!--BLOG_LATEST-->', blog_latest_html(posts))

    sitemap = []
    for v, slug, title, desc, kind in PAGES:
        url = SITE + PATH[v]
        og_rel = 'og/%s.png' % (slug or 'home')
        image = SITE + '/' + og_rel if os.path.exists(os.path.join(ROOT, og_rel)) else SITE + '/og-image.png?v=2'
        page_head = set_meta(head, title, desc, url, image, kind) + jsonld(title, desc, url, image, kind, h1s.get(v), updated)
        body = ''.join(full[x] if x == v else hollowed[x] for x, _, _ in bounds)
        doc = rewrite_links(page_head + pre_main + body + post_main, v, anchors).replace('%%CS_CONFIG%%', config_script(v, anchors))
        dest = os.path.join(OUT, slug, 'index.html') if slug else os.path.join(OUT, 'index.html')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'w', encoding='utf-8').write(doc)
        sitemap.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, updated))

    # 404: every section hollowed and hidden, plus a short note
    links = ''.join('<li><a href="%s">%s</a></li>' % (PATH[p[0]], esc(h1s.get(p[0]) or p[2])) for p in PAGES if p[4] in ('guide', 'tool'))
    nf = ('<section id="view-notfound" class="read"><div class="wrap"><h1>Nothing here</h1>'
          '<p>That page doesn’t exist, or it moved when the site grew up. Try one of these.</p>'
          '<ul>%s</ul><p><a class="btn primary" href="/">Go home</a></p></div></section>\n' % links)
    head404 = set_meta(head, 'Page not found: The Charge Sheet', 'That page does not exist.', SITE + '/404', SITE + '/og-image.png', 'home')
    head404 = head404.replace('content="index, follow, max-image-preview:large"', 'content="noindex"')
    doc = head404 + pre_main + nf + ''.join(hollowed[x] for x, _, _ in bounds) + post_main
    doc = rewrite_links(doc, 'notfound', anchors).replace('%%CS_CONFIG%%', config_script('notfound', anchors))
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(doc)

    # blog
    hollow_all = ''.join(hollowed[x] for x, _, _ in bounds)
    sitemap += build_blog(posts, head, pre_main, post_main, hollow_all, anchors, updated)

    # sitemap, robots, headers, redirects
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % '\n'.join(sitemap))
    shutil.copy(os.path.join(ROOT, 'robots.txt'), os.path.join(OUT, 'robots.txt'))
    headers = open(os.path.join(ROOT, '_headers')).read().rstrip()
    headers += '\n\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n\n/og/*\n  Cache-Control: public, max-age=604800\n'
    open(os.path.join(OUT, '_headers'), 'w').write(headers)
    redirects = ['/index.html / 301']
    for v, slug, *_ in PAGES:
        if slug and v != slug:
            redirects += ['/%s %s 301' % (v, PATH[v]), '/%s/ %s 301' % (v, PATH[v])]
    open(os.path.join(OUT, '_redirects'), 'w').write('\n'.join(redirects) + '\n')

    # static files
    for d in ('fonts', 'img', 'data', 'og'):
        if os.path.isdir(os.path.join(ROOT, d)):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT, d))
    for f in ('favicon.svg', 'favicon-32.png', 'apple-touch-icon.png', 'og-image.png'):
        shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))

    sizes = sorted(os.path.getsize(os.path.join(OUT, p[1], 'index.html') if p[1] else os.path.join(OUT, 'index.html')) for p in PAGES)
    print('Built %d pages into dist/ (updated %s). Page HTML %d to %d KB; CSS %d KB, JS %d KB.' % (
        len(PAGES), updated, sizes[0] // 1024, sizes[-1] // 1024, len(css) // 1024, len(js) // 1024))


if __name__ == '__main__':
    build()

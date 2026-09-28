"""
blog.py

Reads posts/*.md and turns them into data the site build can render.
Standard library only, so it runs on Cloudflare Pages without installs.

A post is a Markdown file named YYYY-MM-DD-some-slug.md with a small header:

    ---
    title: Demand charges ate my margin
    description: One or two sentences for search results and link previews.
    date: 2026-10-06
    tags: [demand charges, utilities]
    kind: essay            # essay (default) or weekly
    draft: true            # optional; drafts only appear on preview deployments
    publish: 2026-10-06T09:00:00-05:00   # optional; hidden on the live site until
                           # this time (then a rebuild publishes it; see
                           # .github/workflows/scheduled-publish.yml)
    image: /og/blog-demand-charges.png   # optional preview image
    art: fleet             # optional header art: a site spot name (see spots.py)
                           # or posts/art/<name>.svg; defaults to posts/art/<slug>.svg
    ---

    The post, in Markdown.

Supported Markdown: headings, paragraphs, bold, italic, links, images, inline
code, code blocks, block quotes, bullet and numbered lists, horizontal rules,
simple pipe tables, and raw HTML blocks (a line that starts with "<").

Blog extras, each on a line of its own:

    {{art ramp-vs-forecast | Caption, in Markdown.}}
        An animated line-art figure from posts/art/ramp-vs-forecast.svg. It plays
        when scrolled into view (the site's spot classes: d, fade, grow, growx,
        flow, ping, bob). The caption doubles as the figure's accessible label.

    {{photo /img/blog/depot.jpg | Alt text | Photo: Name on [Unsplash](https://unsplash.com/...)}}
        A photo with a credit line. Keep photos in img/blog/.
"""
import datetime, html, os, re

ART_DIR = None  # set by load_posts: <root>/posts/art


def art_svg(name):
    """The raw <svg> for posts/art/<name>.svg, or '' if there isn't one."""
    if not ART_DIR or not re.match(r'^[a-z0-9-]+$', name or ''):
        return ''
    path = os.path.join(ART_DIR, name + '.svg')
    if not os.path.exists(path):
        return ''
    svg = open(path, encoding='utf-8').read().strip()
    svg = re.sub(r'<\?xml.*?\?>|<!--.*?-->', '', svg, flags=re.S).strip()
    return re.sub(r'>\s+<', '><', svg)


def strip_tags(t):
    return re.sub(r'<[^>]+>', '', t)


WORDS_PER_MIN = 230


# ---------- front matter ----------
def parse_front_matter(text):
    meta, body = {}, text
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            block, body = text[3:end], text[end + 4:]
            for line in block.strip().splitlines():
                if not line.strip() or line.strip().startswith('#') or ':' not in line:
                    continue
                k, v = line.split(':', 1)
                v = re.sub(r'\s+#.*$', '', v).strip()
                if v.startswith('[') and v.endswith(']'):
                    v = [x.strip().strip('"\'') for x in v[1:-1].split(',') if x.strip()]
                elif v.lower() in ('true', 'false'):
                    v = v.lower() == 'true'
                else:
                    v = v.strip('"\'')
                meta[k.strip().lower()] = v
    return meta, body.lstrip('\n')


# ---------- markdown ----------
def inline(t):
    """Inline Markdown to HTML. Escapes everything that isn't markup."""
    codes = []

    def keep_code(m):
        codes.append('<code>%s</code>' % html.escape(m.group(1)))
        return '\x00%d\x00' % (len(codes) - 1)
    t = re.sub(r'`([^`]+)`', keep_code, t)
    t = html.escape(t, quote=False)
    t = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;([^&]*)&quot;)?\)',
               lambda m: '<img src="%s" alt="%s" loading="lazy">' % (m.group(2), m.group(1)), t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
               lambda m: '<a href="%s"%s>%s</a>' % (m.group(2), ' rel="noopener"' if m.group(2).startswith('http') else '', m.group(1)), t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    t = re.sub(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])', r'<em>\1</em>', t)
    t = re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], t)
    return t


def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', re.sub(r'<[^>]+>', '', t).lower()).strip('-')


def markdown(md):
    lines = md.replace('\r\n', '\n').split('\n')
    out, i, n = [], 0, len(lines)

    def is_block_start(l):
        return (re.match(r'^(#{1,6})\s', l) or re.match(r'^\s*([-*+]|\d+\.)\s', l) or l.startswith('>')
                or l.startswith('```') or re.match(r'^(-{3,}|\*{3,})\s*$', l) or l.startswith('<') or l.startswith('{{')
                or (l.startswith('|') and l.rstrip().endswith('|')))

    while i < n:
        l = lines[i]
        if not l.strip():
            i += 1
            continue
        m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', l)
        if m:
            lvl = max(2, len(m.group(1)))  # the page already has the only h1
            text = inline(m.group(2))
            out.append('<h%d id="%s">%s</h%d>' % (lvl, slugify(text), text, lvl))
            i += 1
            continue
        if l.startswith('```'):
            lang = l[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].startswith('```'):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append('<pre><code%s>%s</code></pre>' % (' class="language-%s"' % html.escape(lang) if lang else '', html.escape('\n'.join(buf))))
            continue
        if re.match(r'^(-{3,}|\*{3,})\s*$', l):
            out.append('<hr>')
            i += 1
            continue
        m = re.match(r'^\{\{\s*art\s+([a-z0-9-]+)\s*(?:\|\s*(.*?))?\s*\}\}\s*$', l)
        if m:
            svg = art_svg(m.group(1))
            if not svg:
                raise SystemExit('blog: missing posts/art/%s.svg' % m.group(1))
            cap = inline(m.group(2) or '')
            label = html.escape(strip_tags(cap), quote=True)
            out.append('<figure class="post-fig"><div class="spot io" role="img"%s>%s</div>%s</figure>' % (
                ' aria-label="%s"' % label if label else ' aria-hidden="true"', svg,
                '<figcaption>%s</figcaption>' % cap if cap else ''))
            i += 1
            continue
        m = re.match(r'^\{\{\s*photo\s+(\S+)\s*\|\s*(.*?)\s*(?:\|\s*(.*?))?\s*\}\}\s*$', l)
        if m:
            out.append('<figure class="post-photo"><img src="%s" alt="%s" loading="lazy">%s</figure>' % (
                html.escape(m.group(1), quote=True), html.escape(m.group(2), quote=True),
                '<figcaption>%s</figcaption>' % inline(m.group(3)) if m.group(3) else ''))
            i += 1
            continue
        if l.startswith('<'):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append('\n'.join(buf))
            continue
        if l.startswith('>'):
            buf = []
            while i < n and lines[i].startswith('>'):
                buf.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            out.append('<blockquote>%s</blockquote>' % markdown('\n'.join(buf)))
            continue
        if l.startswith('|') and l.rstrip().endswith('|'):
            rows = []
            while i < n and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            head, body = rows[0], rows[1:]
            if body and all(re.match(r'^:?-+:?$', c) for c in body[0]):
                body = body[1:]
            t = '<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                ''.join('<th>%s</th>' % inline(c) for c in head),
                ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in body))
            out.append(t)
            continue
        m = re.match(r'^\s*([-*+]|\d+\.)\s+', l)
        if m:
            ordered = m.group(1)[0].isdigit()
            items = []
            while i < n and lines[i].strip():
                mm = re.match(r'^\s*([-*+]|\d+\.)\s+(.*)$', lines[i])
                if mm:
                    items.append(mm.group(2))
                elif items:
                    items[-1] += ' ' + lines[i].strip()
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % inline(x) for x in items), tag))
            continue
        buf = []
        while i < n and lines[i].strip() and not (buf and is_block_start(lines[i])):
            buf.append(lines[i].strip())
            i += 1
        out.append('<p>%s</p>' % inline(' '.join(buf)))
    return '\n'.join(out)


# ---------- posts ----------
def now_utc():
    """Build time, or BLOG_NOW (ISO 8601) to preview a future build."""
    fake = os.environ.get('BLOG_NOW')
    t = parse_time(fake) if fake else None
    return t or datetime.datetime.now(datetime.timezone.utc)


def parse_time(v):
    """ISO 8601 date or datetime -> aware UTC datetime (a bare date means 9:00 Central)."""
    v = str(v or '').strip()
    if not v:
        return None
    if re.match(r'^\d{4}-\d{2}-\d{2}$', v):
        v += 'T09:00:00-05:00'
    t = datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
    if t.tzinfo is None:
        t = t.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
    return t.astimezone(datetime.timezone.utc)


def show_drafts():
    if os.environ.get('SHOW_DRAFTS') == '1':
        return True
    branch = os.environ.get('CF_PAGES_BRANCH')
    return bool(branch) and branch != 'main'


def load_posts(root):
    folder = os.path.join(root, 'posts')
    posts = []
    if not os.path.isdir(folder):
        return posts
    drafts_ok = show_drafts()
    global ART_DIR
    ART_DIR = os.path.join(folder, 'art')
    for name in sorted(os.listdir(folder)):
        m = re.match(r'^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$', name)
        if not m:
            continue
        meta, body = parse_front_matter(open(os.path.join(folder, name), encoding='utf-8').read())
        draft = bool(meta.get('draft'))
        publish = parse_time(meta.get('publish'))
        scheduled = bool(publish and publish > now_utc())
        if (draft or scheduled) and not drafts_ok:
            continue
        date = str(meta.get('date') or m.group(1))
        words = len(re.findall(r'\w+', body))
        tags = meta.get('tags') or []
        if isinstance(tags, str):
            tags = [x.strip() for x in tags.split(',') if x.strip()]
        posts.append({
            'slug': m.group(2), 'file': name, 'title': meta.get('title') or m.group(2).replace('-', ' ').capitalize(),
            'description': meta.get('description', ''), 'date': date, 'updated': str(meta.get('updated') or date),
            'tags': tags, 'kind': meta.get('kind', 'essay'), 'draft': draft or scheduled,
            'scheduled': str(meta.get('publish'))[:10] if scheduled and not draft else '', 'image': meta.get('image', ''),
            'minutes': max(1, round(words / WORDS_PER_MIN)), 'html': markdown(body),
            'art': header_art(meta.get('art'), m.group(2), meta.get('kind', 'essay')),
        })
        # Feed readers don't get the site's CSS, so figures become their captions.
        posts[-1]['feed_html'] = re.sub(
            r'<figure class="post-fig">.*?</div>(?:<figcaption>(.*?)</figcaption>)?</figure>',
            lambda mm: '<p><em>%s</em></p>' % mm.group(1) if mm.group(1) else '', posts[-1]['html'], flags=re.S)
    posts.sort(key=lambda p: (p['date'], p['slug']), reverse=True)
    return posts


def header_art(name, slug, kind):
    """Header illustration for a post: posts/art/<name or slug>.svg, else a site spot, else the blog spot."""
    import spots
    svg = art_svg(name or slug)
    if svg:
        return '<div class="spot" aria-hidden="true">%s</div>' % svg
    if name and name in spots.SPOTS:
        return spots.SPOTS[name]
    return spots.BLOG


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime('%B ') + str(d.day) + d.strftime(', %Y')

"""Which blog posts are due but not live yet? Used by the scheduled-publish workflow.

Prints `missing=<slugs>` (space separated, empty if nothing to do) for $GITHUB_OUTPUT.
A post is due when it isn't a draft and its `publish:` time (if any) has passed.
It's live when its URL appears in the live RSS feed.
"""
import os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import blog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.environ.get('FEED_URL', 'https://chargesheet.io/blog/feed.xml')


def due_slugs():
    now = blog.now_utc()
    out = []
    folder = os.path.join(ROOT, 'posts')
    for name in sorted(os.listdir(folder)):
        m = re.match(r'^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md$', name)
        if not m:
            continue
        meta, _ = blog.parse_front_matter(open(os.path.join(folder, name), encoding='utf-8').read())
        if meta.get('draft'):
            continue
        t = blog.parse_time(meta.get('publish'))
        if t is None or t <= now:
            out.append(m.group(2))
    return out


def main():
    due = due_slugs()
    try:
        req = urllib.request.Request(FEED, headers={'User-Agent': 'charge-sheet-scheduler'})
        feed = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
    except Exception as e:  # can't see the live site: rebuild to be safe
        print('feed unreachable: %s' % e, file=sys.stderr)
        print('missing=%s' % ' '.join(due))
        return
    missing = [s for s in due if '/blog/%s/' % s not in feed]
    print('due: %s' % (', '.join(due) or 'none'), file=sys.stderr)
    print('missing=%s' % ' '.join(missing))


if __name__ == '__main__':
    main()

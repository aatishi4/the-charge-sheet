#!/usr/bin/env python3
"""
build_incentives.py

Builds the static rebate lookup the home side uses ("Rebates by ZIP", Start here, the
apartment and HOA guide) from the U.S. Department of Energy's Alternative Fuels Data
Center (AFDC) laws and incentives pages. Public data, no API key.

For each state it keeps:
  - state incentives that apply to homes and drivers (charger rebates, EV rebates, perks),
  - every utility's residential EV programs (charger, rate and vehicle incentives),
    matched to the EIA utility ids the ZIP lookup in data/rates/ already uses,
  - the state's charging laws for renters, condos and HOAs (right to charge).

Output (static files, fetched by the browser on demand):
  data/incentives/<ST>.json   one state
  data/incentives/zip3.json   first three ZIP digits -> state (from data/rates)
  data/incentives/meta.json   build date, counts per state, sources

    python3 tools/build_incentives.py                 # fetch from afdc.energy.gov
    python3 tools/build_incentives.py --seed pages.json   # use saved pages {path: html} first, fetch the rest
    python3 tools/build_incentives.py --save pages.json   # also save every page it fetched

Standard library only. Run weekly by .github/workflows/refresh-incentives.yml. If AFDC is
unreachable or a page fails to parse, that state keeps its last good file.
"""
import datetime, glob, html, json, os, re, sys, time, urllib.request
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'incentives')
RATES = os.path.join(ROOT, 'data', 'rates')
BASE = 'https://afdc.energy.gov'
UA = {'User-Agent': 'chargesheet.io incentive snapshot, weekly (github.com/aatishi4/the-charge-sheet)'}
STATES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado',
          'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia',
          'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky',
          'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
          'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
          'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
          'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
          'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
          'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'}

PAGES = {}       # path -> html (seeded or fetched)
FETCHED = {}     # path -> html fetched this run (for --save)
NET = {'ok': True}


def get(path):
    if path in PAGES:
        return PAGES[path]
    if not NET['ok']:
        return None
    for i in range(3):
        try:
            req = urllib.request.Request(BASE + path, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                h = r.read().decode('utf-8', 'replace')
            PAGES[path] = FETCHED[path] = h
            time.sleep(0.4)  # be polite: one page at a time
            return h
        except Exception as e:
            print('  fetch failed (%s): %s' % (e, path), file=sys.stderr)
            time.sleep(4 * (i + 1))
    return None


def text(h):
    """HTML fragment -> plain text with paragraph breaks."""
    h = re.sub(r'(?is)<(script|style).*?</\1>', ' ', h or '')
    h = re.sub(r'(?i)</(p|li|tr|h\d|div)>|<br\s*/?>', '\n', h)
    h = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    h = re.sub(r'[ \t\r\f\v]+', ' ', h)
    return re.sub(r'\n\s*\n+', '\n', h).strip()


def clip(t, n=320):
    """First sentences up to n characters, ending on a sentence."""
    t = re.sub(r'\s+', ' ', re.sub(r'\(Reference .*?\)\s*$', '', t.strip())).strip()
    if len(t) <= n:
        return t
    cut = t[:n]
    m = list(re.finditer(r'[.;](?=\s)', cut))
    return (cut[:m[-1].end()] if m and m[-1].end() > 80 else cut.rsplit(' ', 1)[0] + '...').strip()


# ---------- parsers (regex over AFDC's server-rendered markup; checked against saved pages) ----------
def parse_summary(h):
    """/laws/state_summary?state=XX -> items [{id,title,tech,sec}], utility ids, last review."""
    marks = [(m.start(), html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip())
             for m in re.finditer(r'(?is)<h[23][^>]*>(.*?)</h[23]>', h)]
    items = []
    for m in re.finditer(r'(?is)<li class="law-list-item"([^>]*)>\s*<a href="/laws/(\d+)">(.*?)</a>', h):
        attrs, lid, title = m.group(1), int(m.group(2)), html.unescape(m.group(3)).strip()
        tm = re.search(r'data-technology="([^"]*)"', attrs)
        try:
            tech = json.loads(html.unescape(tm.group(1))) if tm else []
        except ValueError:
            tech = []
        sec = ''
        for pos, name in marks:
            if pos < m.start() and name in ('State Incentives', 'Laws and Regulations', 'Utility / Private Incentives'):
                sec = name
        items.append({'id': lid, 'title': title, 'tech': tech, 'sec': sec})
    utils = [{'id': int(a), 'name': html.unescape(b).strip()}
             for a, b in re.findall(r'(?is)<a href="/laws/utilities/(\d+)">(.*?)</a>', h)]
    rv = re.search(r'Last Comprehensive Review:\s*([A-Za-z]+ \d{4})', text(h))
    return items, utils, rv.group(1) if rv else ''


def parse_all(h):
    """/laws/all?state=XX -> {section: [(title, html)]} for the three law sections."""
    out = {}
    heads = list(re.finditer(r'(?is)<h2 id="([^"]+)">(.*?)</h2>', h))
    for i, m in enumerate(heads):
        name = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
        if name not in ('State Incentives', 'Utility / Private Incentives', 'Laws and Regulations'):
            continue
        end = heads[i + 1].start() if i + 1 < len(heads) else len(h)
        nxt = re.search(r'(?is)<h2[ >]', h[m.end():end])
        chunk = h[m.end():m.end() + nxt.start()] if nxt else h[m.end():end]
        parts = re.split(r'(?is)<h3>(.*?)</h3>', chunk)
        out[name] = [(html.unescape(re.sub(r'<[^>]+>', '', parts[j])).strip(), parts[j + 1]) for j in range(1, len(parts) - 1, 2)]
    return out


def parse_utility(title, h):
    """One utility block from the 'all' page -> residential programs by topic."""
    t = text(h)
    kind = ''
    km = re.search(r'is\s+(an?\s+.+?)\s+that operates', re.sub(r'\s+', ' ', t))
    if km:
        k = km.group(1).lower()
        kind = ('Investor-owned utility' if 'investor' in k else 'Cooperative' if 'cooperative' in k else
                'Municipal utility' if 'municipal' in k or 'public power' in k else
                'Public utility district' if 'public utility district' in k else k[2:].strip().capitalize())
    web = ''
    wm = re.search(r'(?is)<p>.*?<a href="([^"]+)"', h)
    if wm:
        web = html.unescape(wm.group(1))
    res = {}
    rm = re.search(r'(?is)Residential Incentives</h4>(.*?)(?:<h4|$)', h)
    if rm:
        for topic, body in re.findall(r'(?is)<strong>(.*?)</strong>(.*?)(?=<strong>|$)', rm.group(1)):
            lis = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'(?is)<li>(.*?)</li>', body)]
            if lis:
                res[html.unescape(topic).strip()] = lis
    name = re.sub(r'\s+-\s+[^-]+$', '', title).strip()
    return {'name': name, 'kind': kind, 'web': web, 'res': res}


def parse_law(h):
    """/laws/<id> -> title, plain text, type, technologies."""
    tm = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', h)
    bm = re.search(r'(?is)<div class="col-md-8">(.*?)</div>\s*<div class="col-md-4">', h)
    meta = text(h[bm.end():bm.end() + 3000]) if bm else ''
    ty = re.search(r'Type:\s*(.+)', meta)
    te = re.search(r'Technologies:\s*(.+)', meta)
    return {'title': html.unescape(re.sub(r'<[^>]+>', '', tm.group(1))).strip() if tm else '',
            'html': bm.group(1) if bm else '', 'type': ty.group(1).strip() if ty else '',
            'tech': te.group(1).strip() if te else ''}


# ---------- what counts for a household ----------
HOME = re.compile(r'\b(residen\w*|homeowners?|home charg\w*|at home|household\w*|individuals?\b|single-family|multi-?family|'
                  r'multi-unit|multi-dwelling|apartments?|tenants?|renters?|condominiums?|personal (?:vehicle|use)|'
                  r'vehicle owners?|low-income|income-qualified|dwelling|private (?:citizens?|individuals?))', re.I)
NOT_HOME = re.compile(r'(School Bus|Transit|Fleet|Manufactur|NEVI|Truck|Port\b|Government|State Agency|Workforce|'
                      r'Heavy|Medium-|Idle|Biofuel|Ethanol|Biodiesel|Natural Gas|Propane|Hydrogen|Airport|Marine|'
                      r'Planning|Research|Dealer|Corridor|Electrification Plan|Mitigation Trust|Utility Program|Commercial|Public|'
                      r'Workplace|Business|Nonprofit|Warehouse|Highway|State Park|Retail)', re.I)
RTC = re.compile(r'(Policies for (?:Condo|Multi|Rent|Renter|Residential Assoc|Association|Housing Assoc|Homeowner)|'
                 r'Planned Communities|Right to Charge|Renters|Rental Propert|Tenants)', re.I)
NEWBUILD = re.compile(r'(Building Standard|New Build|Make-Ready Requirement|Residential .*Charger (?:Standard|Installation Polic))', re.I)


def kind_of(title, t):
    s = title + ' ' + t
    if re.search(r'charg(?:er|ing station|ing equipment)|EVSE|make-ready|wiring', s, re.I):
        return 'charger'
    if re.search(r'time-of-use|\bTOU\b|electricity rate|rate discount', s, re.I):
        return 'rate'
    if re.search(r'(rebate|tax credit|voucher|grant|incentive).{0,80}(vehicle|EV\b)|(vehicle|EV\b).{0,80}(rebate|tax credit|voucher)', s, re.I):
        return 'vehicle'
    return 'perk'


def more_link(h):
    for href, label in re.findall(r'(?is)<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', h or ''):
        href = html.unescape(href)
        if href.startswith('http') and 'afdc.energy.gov' not in href and not re.search(r'(legislature|ilga\.gov|leg\.|legis|statute|law\.|codes?\.|/bills?/|\.pdf$)', href, re.I):
            return href
    return ''


# ---------- EIA utility matching ----------
STOP = set('company co inc incorporated corp corporation llc lp the of and electric electrical electricity power energy '
           'light lighting utilities utility service services public cooperative coop association assn membership '
           'municipal board department dept commission system systems district authority rural plant plants works water '
           'gas city town village county borough township commonwealth peoples ut light&power l&p p&l inc. & - mun elec pwr'.split())
STATE_WORDS = set(w.lower() for n in STATES.values() for w in n.split())
ALIAS = {  # AFDC brand name -> words that appear in the EIA legal name
    'xcel': ['public service co of colorado', 'northern states power', 'southwestern public service'],
    'comed': ['commonwealth edison'], 'pg&e': ['pacific gas'], 'pge': ['portland general'],
    'sce': ['southern california edison'], 'sdg&e': ['san diego gas'], 'dominion': ['virginia electric', 'dominion energy south carolina'],
    'ameren missouri': ['union electric'], 'appalachian power': ['appalachian power'], 'pse': ['puget sound energy'],
    'bge': ['baltimore gas'], 'pepco': ['potomac electric'], 'pseg': ['public service elec', 'pse&g', 'long island'],
    'con edison': ['consolidated edison'], 'national grid': ['niagara mohawk', 'massachusetts electric', 'narragansett'], 'unitil': ['unitil'],
    'eversource': ['connecticut light', 'nstar', 'public service co of nh', 'western massachusetts'],
    'jcp&l': ['jersey central'], 'fpl': ['florida power & light', 'florida power and light'],
    'tep': ['tucson electric'], 'aps': ['arizona public service'], 'srp': ['salt river project'],
    'smud': ['sacramento municipal'], 'ladwp': ['los angeles department of water'], 'tva': ['tennessee valley'],
    'entergy': ['entergy'], 'evergy': ['evergy', 'kansas city power', 'westar'], 'oncor': ['oncor'],
    'swepco': ['southwestern electric power'], 'duke energy': ['duke energy'], 'santee cooper': ['south carolina public service'],
    'pse&g': ['public service elec', 'public service electric'], 'rocky mountain power': ['pacificorp'],
    'pacific power': ['pacificorp'], 'minnesota power': ['allete', 'minnesota power'], 'cps energy': ['san antonio'],
    'memphis light': ['memphis'], 'austin energy': ['austin'], 'seattle city light': ['seattle'],
    'nv energy': ['nevada power', 'sierra pacific'], 'idaho power': ['idaho power'], 'dte': ['dte electric'],
    'consumers energy': ['consumers energy'], 'we energies': ['wisconsin electric'], 'alliant': ['interstate power', 'wisconsin power'],
    'firstenergy': ['ohio edison', 'cleveland electric', 'toledo edison', 'pennsylvania electric', 'metropolitan edison', 'west penn', 'penn power', 'jersey central', 'monongahela', 'potomac edison'],
    'aep': ['ohio power', 'appalachian power', 'indiana michigan', 'kentucky power', 'public service co of oklahoma', 'southwestern electric power'],
}


EXPAND = {'el': 'electric', 'elec': 'electric', 'member': 'membership', 'memb': 'membership', 'comm': 'commission',
          'util': 'utility', 'utils': 'utility', 'dist': 'district', 'dt': 'district', 'assn': 'association',
          'emc': 'electric membership corporation', 'remc': 'rural electric membership corporation',
          'pud': 'public utility district', 'st': 'saint', 'mtn': 'mountain', 'svc': 'service', 'svcs': 'services'}
LEGAL = set('company co inc incorporated corp corporation llc lp the of and'.split())


def toks(name):
    """(core, distinctive, aliases): core drops only legal words; distinctive also drops generic utility words,
    state names and short tokens; aliases are the acronyms in parentheses, e.g. ComEd, OUC."""
    s = name.lower().replace('&', ' and ').replace("'", '')
    alias = set()
    for a in re.findall(r'\(([^)]+)\)', s):
        alias |= set(w for w in re.sub(r'[^a-z0-9 ]+', ' ', a).split() if len(w) > 1)
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'\bco-op\b|\bcoop\b', 'cooperative', s)
    words = []
    for w in re.sub(r'[^a-z0-9 ]+', ' ', s).split():
        words += EXPAND.get(w, w).split()
    core = set(w for w in words if w not in LEGAL)
    dist = set(w for w in core if w not in STOP and w not in STATE_WORDS and len(w) > 2 and not w.isdigit()
               and w not in ('number', 'saint', 'county', 'no'))
    return core, dist, alias - STOP


NOT_ELECTRIC = re.compile(r'propane|soybean|natural gas|gas service|\bfuels?\b|gas association|corn growers', re.I)


def load_eia():
    """EIA utilities from data/rates/u, plus each one's states (from the ZIP shards)."""
    us = {}
    for p in glob.glob(os.path.join(RATES, 'u', '*.json')):
        try:
            u = json.load(open(p, encoding='utf-8'))
            us[u['eiaid']] = {'id': u['eiaid'], 'name': u.get('utility', ''), 'state': u.get('state', '')}
        except Exception:
            pass
    return us


def zip3_map(eia):
    """First three ZIP digits -> state (majority of the first-listed utility's state), and the states
    each EIA utility actually serves (a utility's own record carries only one state)."""
    votes, zips = defaultdict(Counter), {}
    for p in glob.glob(os.path.join(RATES, 'zip', '*.json')):
        z3 = os.path.basename(p)[:3]
        try:
            m = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        zips[z3] = m
        for z, ids in m.items():
            st = (eia.get(ids[0]) or {}).get('state') if ids else None
            if st:
                votes[z3][st] += 1
    z3st = {z3: c.most_common(1)[0][0] for z3, c in sorted(votes.items())}
    serves = defaultdict(set)
    for z3, m in zips.items():
        st = z3st.get(z3)
        if not st:
            continue
        for ids in m.values():
            for i in ids:
                serves[i].add(st)
    return z3st, serves


WEAK = set('north south east west northern southern eastern western central valley united consolidated great lakes '
           'pacific mountain river rural new'.split())


def match_eia(name, st, eia_by_state):
    """EIA ids of the utilities an AFDC utility name refers to, within one state. Brand names go through ALIAS;
    otherwise the distinctive words must agree (one side may add only generic words)."""
    core_a, dist_a, alias_a = toks(name)
    low = name.lower()
    keys = [k for k in ALIAS if re.search(r'(^|[^a-z&])' + re.escape(k) + r'($|[^a-z&])', low)]
    strong_a = dist_a - WEAK
    hits = []
    for u in eia_by_state.get(st, []):
        en = re.sub(r'^(the|city of|town of|village of|city and county of|city & county of) ', '', u['name'].lower())
        core_b, dist_b, _ = toks(u['name'])
        if keys:
            ok = any(en.startswith(w) for k in keys for w in ALIAS[k])
        elif strong_a:
            if dist_a == dist_b:
                ok = True
            elif dist_a < dist_b:
                ok = bool(strong_a & dist_b) and (dist_b - dist_a) <= WEAK
            elif dist_b < dist_a:
                ok = len(dist_b) >= 2 and bool(dist_b - WEAK)
            else:
                ok = False
        else:
            ok = len(core_a) >= 2 and core_a <= core_b and (core_b - core_a) <= STOP
        if not ok and alias_a and (alias_a & dist_b):
            ok = True
        if ok:
            hits.append(u['id'])
    return hits


# ---------- build ----------
def build_state(st, eia_by_state):
    sh = get('/laws/state_summary?state=' + st)
    ah = get('/laws/all?state=' + st)
    if not sh or not ah:
        raise RuntimeError('pages unavailable')
    items, util_ids, review = parse_summary(sh)
    secs = parse_all(ah)
    if not items and not secs:
        raise RuntimeError('nothing parsed')
    texts = {}
    for sec in ('State Incentives', 'Laws and Regulations'):
        for title, h in secs.get(sec, []):
            texts[title] = h
    by_title = {i['title']: i for i in items}
    # items the summary missed but the 'all' page has (and vice versa) both count
    pool = [dict(i) for i in items]
    for sec in ('State Incentives', 'Laws and Regulations'):
        for title, h in secs.get(sec, []):
            if title not in by_title:
                pool.append({'id': None, 'title': title, 'tech': [], 'sec': sec})
    inc, laws = [], []
    for it in pool:
        title, sec = it['title'], it['sec']
        ev = (not it['tech']) or ('ELEC' in it['tech'] or 'PHEV' in it['tech'])
        want_inc = sec == 'State Incentives' and ev and not NOT_HOME.search(title)
        want_law = sec == 'Laws and Regulations' and ev and not re.search(r'Study|Assessment|Pilot', title) and (
            RTC.search(title) or (NEWBUILD.search(title) and not NOT_HOME.search(title)))
        if not (want_inc or want_law):
            continue
        h = texts.get(title)
        if h is None and it['id']:
            page = get('/laws/%d' % it['id'])
            if page:
                h = parse_law(page)['html']
        if h is None:
            continue
        t = text(h)
        if want_inc and not it['tech'] and not re.search(r'electric vehicle|\bEVs?\b|plug-in|charg', t, re.I):
            continue
        if want_inc and not HOME.search(t) and not HOME.search(title):
            continue
        row = {'id': it['id'], 'title': title, 'sum': clip(t), 'more': more_link(h) if want_inc else ''}
        if want_inc:
            row['kind'] = kind_of(title, t)
            inc.append(row)
        else:
            row['kind'] = 'rtc' if RTC.search(title) else 'newbuild'
            ref = re.findall(r'\(Reference (.+?)\)', t.replace('\n', ' '))
            row['ref'] = re.sub(r'\s+', ' ', ref[-1]).strip() if ref else ''
            laws.append(row)
    order = {'charger': 0, 'rate': 1, 'vehicle': 2, 'perk': 3}
    inc.sort(key=lambda r: (order.get(r['kind'], 9), r['title']))
    uid = {u['name'].lower(): u['id'] for u in util_ids}
    utils = []
    for title, h in secs.get('Utility / Private Incentives', []):
        u = parse_utility(title, h)
        if not u['res'] or NOT_ELECTRIC.search(u['name']):
            continue
        u['afdc'] = uid.get(u['name'].lower())
        u['eia'] = match_eia(u['name'], st, eia_by_state)
        utils.append(u)
    return {'st': st, 'name': STATES[st], 'review': review, 'state': inc, 'laws': laws, 'utils': utils}


def main(argv):
    seed = save = None
    if '--seed' in argv:
        seed = argv[argv.index('--seed') + 1]
        PAGES.update(json.load(open(seed, encoding='utf-8')))
    if '--save' in argv:
        save = argv[argv.index('--save') + 1]
    if '--offline' in argv:
        NET['ok'] = False
    only = [a.upper() for a in argv if re.fullmatch(r'[A-Za-z]{2}', a)]
    os.makedirs(OUT, exist_ok=True)
    eia = load_eia()
    z3, serves = zip3_map(eia)
    eia_by_state = defaultdict(list)
    for u in eia.values():
        for st in (serves.get(u['id']) or {u['state']}):
            eia_by_state[st].append(u)
    today = datetime.date.today().isoformat()
    meta_path = os.path.join(OUT, 'meta.json')
    try:
        meta = json.load(open(meta_path, encoding='utf-8'))
    except Exception:
        meta = {}
    counts, failed, unmatched = meta.get('states', {}), [], []
    built_states = {}
    for st in (only or list(STATES)):
        try:
            built_states[st] = build_state(st, eia_by_state)
        except Exception as e:
            print('  %s: kept last good file (%s)' % (st, e), file=sys.stderr)
            failed.append(st)
    matched_somewhere = set(u['name'].lower() for d in built_states.values() for u in d['utils'] if u['eia'])
    for st, d in built_states.items():
        d['utils'] = [u for u in d['utils'] if u['eia'] or u['name'].lower() not in matched_somewhere]
        path = os.path.join(OUT, st + '.json')
        try:
            old = json.load(open(path, encoding='utf-8'))
        except Exception:
            old = None
        if old and {k: v for k, v in old.items() if k != 'checked'} == d:
            d = old  # nothing changed: keep the file, and the date it last changed, as it is
        else:
            d['checked'] = today
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
        counts[st] = {'state': len(d['state']), 'utils': len(d['utils']), 'rtc': sum(1 for l in d['laws'] if l['kind'] == 'rtc'),
                      'review': d['review'], 'chargerUtils': sum(1 for u in d['utils'] if u['res'].get('Infrastructure'))}
        unmatched += ['%s: %s' % (st, u['name']) for u in d['utils'] if not u['eia']]
        print('%s  %2d state, %2d utilities (%d unmatched), %d laws' % (
            st, len(d['state']), len(d['utils']), sum(1 for u in d['utils'] if not u['eia']), len(d['laws'])))
    if z3:
        with open(os.path.join(OUT, 'zip3.json'), 'w', encoding='utf-8') as f:
            json.dump(z3, f, separators=(',', ':'))
    built = today if len(failed) < len(only or STATES) else meta.get('built', today)
    if meta.get('states') == counts and meta.get('failed') == failed:
        built = meta.get('built', built)  # unchanged: don't touch meta.json, so the weekly run commits nothing
    meta = {'built': built, 'states': counts, 'failed': failed,
            'source': {'name': 'U.S. Department of Energy, Alternative Fuels Data Center: Federal and State Laws and Incentives',
                       'url': BASE + '/laws', 'license': 'Public domain (U.S. government work)'}}
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, sort_keys=True)
    if unmatched:
        print('Utilities not matched to an EIA id (shown statewide only): %d' % len(unmatched), file=sys.stderr)
    if save:
        json.dump(FETCHED, open(save, 'w', encoding='utf-8'))
    ok = len(STATES if not only else only) - len(failed)
    print('Built %d of %d states, %d ZIP prefixes. %d utilities unmatched.' % (ok, len(only or STATES), len(z3), len(unmatched)))
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])

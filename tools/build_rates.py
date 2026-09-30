#!/usr/bin/env python3
"""
build_rates.py

Builds the static ZIP-code rate lookup the home charging calculator uses, from two
free public datasets (both CC BY 4.0, no API key):

  1. EIA Form 861 "U.S. Electric Utility Companies and Rates: Look-up by Zip Code"
     (OpenEI OEDI): which utilities serve each ZIP, and each utility's average
     residential price.
  2. The OpenEI U.S. Utility Rate Database (URDB) bulk download: the actual
     residential rate plans, including time-of-use schedules.

Output (served as static files, fetched by the browser on demand):
  data/rates/zip/<first 3 digits>.json   {"60477": [eiaid, ...], ...}
  data/rates/u/<eiaid>.json              {"eiaid", "utility", "res", "items": [URDB-shaped plans]}
  data/rates/meta.json                   sources, dates, counts

    python3 tools/build_rates.py                      # download both datasets, then build
    python3 tools/build_rates.py --zip a.csv b.csv --urdb usurdb.csv.gz   # from local files

Standard library only. Run yearly by .github/workflows/refresh-rates.yml.
"""
import csv, datetime, gzip, io, json, os, re, shutil, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'rates')
UA = {'User-Agent': 'chargesheet.io rate snapshot (github.com/aatishi4/the-charge-sheet)'}
ZIP_PAGES = ['https://data.openei.org/submissions/8563']          # 2024 edition; add newer editions first
URDB_PAGE = 'https://data.openei.org/submissions/5'
URDB_FALLBACK = ['https://openei.org/apps/USURDB/download/usurdb.csv.gz']
MAX_PLANS = 12
csv.field_size_limit(1 << 30)


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:
            print('  fetch failed (%s): %s' % (e, url), file=sys.stderr)
            time.sleep(3 * (i + 1))
    raise SystemExit('could not download ' + url)


def links(page):
    html = fetch(page).decode('utf-8', 'replace')
    out = []
    for h in re.findall(r'href="([^"]+)"', html):
        if h.startswith('/'):
            h = 'https://data.openei.org' + h
        out.append(h.replace('&amp;', '&'))
    return out


def discover_zip_csvs():
    for page in ZIP_PAGES:
        found = [u for u in links(page) if re.search(r'zip_?codes?[^/]*\.csv', u, re.I)]
        found = sorted(set(found))
        if found:
            print('ZIP files: ' + ', '.join(found))
            return found
        print('  no ZIP CSV links on %s; csv-ish links seen: %s' % (page, [u for u in links(page) if '.csv' in u.lower() or 'zip' in u.lower()][:15]))
    raise SystemExit('no ZIP code CSVs found on ' + ', '.join(ZIP_PAGES))


def discover_urdb():
    cands = [u for u in links(URDB_PAGE) if re.search(r'usurdb[^/]*\.csv(\.gz)?$', u, re.I)]
    cands = sorted(set(cands)) + URDB_FALLBACK
    print('URDB candidates: ' + ', '.join(cands))
    return cands[0]


def read_csv_bytes(b, name=''):
    if name.endswith('.gz') or b[:2] == b'\x1f\x8b':
        b = gzip.decompress(b)
    return list(csv.DictReader(io.StringIO(b.decode('utf-8-sig', 'replace'))))


# ---------- EIA-861 ZIP lookup ----------
def num(v):
    try:
        f = float(v)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def build_zip_map(rows):
    zips, util = {}, {}
    for r in rows:
        z = (r.get('zip') or '').strip().zfill(5)
        try:
            eid = int(float(r.get('eiaid') or 0))
        except ValueError:
            continue
        if not re.match(r'^\d{5}$', z) or not eid:
            continue
        zips.setdefault(z, [])
        if eid not in zips[z]:
            zips[z].append(eid)
        u = util.setdefault(eid, {'utility': (r.get('utility_name') or '').strip(), 'state': (r.get('state') or '').strip(), 'res': None})
        res = num(r.get('res_rate'))
        if res and not u['res']:
            u['res'] = round(res, 4)
    return zips, util


# ---------- URDB ----------
def epoch(v):
    v = (v or '').strip()
    if not v:
        return None
    if re.match(r'^\d+(\.\d+)?$', v):
        return float(v)
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.datetime.strptime(v[:19], fmt).replace(tzinfo=datetime.timezone.utc).timestamp()
        except ValueError:
            pass
    return None


def sched(v):
    try:
        s = json.loads((v or '').replace("'", '"'))
    except ValueError:
        return []
    if isinstance(s, list) and len(s) == 12 and all(isinstance(m, list) and len(m) == 24 for m in s):
        return [[int(h) for h in m] for m in s]
    return []


COL = re.compile(r'^energyratestructure/period(\d+)/tier(\d+)(rate|adj|max)$')


def structure(r, keys):
    per = {}
    for k in keys:
        m = COL.match(k)
        if not m:
            continue
        v = r.get(k)
        if v in (None, ''):
            continue
        p, t, f = int(m.group(1)), int(m.group(2)), m.group(3)
        per.setdefault(p, {}).setdefault(t, {})[f] = v
    out = []
    for p in range(0, (max(per) + 1) if per else 0):
        tiers = per.get(p, {})
        row = []
        for t in sorted(tiers)[:3]:
            d = tiers[t]
            try:
                row.append({'rate': float(d.get('rate') or 0), 'adj': float(d.get('adj') or 0), 'max': float(d['max']) if d.get('max') not in (None, '') else None})
            except ValueError:
                pass
        out.append(row)
    return out


def trim(r, keys):
    return {
        'label': r.get('label') or r.get('_id') or '', 'name': (r.get('name') or '').strip(), 'utility': (r.get('utility') or '').strip(),
        'eiaid': int(float(r.get('eiaid') or 0)), 'startdate': epoch(r.get('startdate')), 'enddate': epoch(r.get('enddate')),
        'fixedchargefirstmeter': float(r.get('fixedchargefirstmeter') or 0), 'fixedchargeunits': r.get('fixedchargeunits') or '$/month',
        'energyratestructure': structure(r, keys),
        'energyweekdayschedule': sched(r.get('energyweekdayschedule')), 'energyweekendschedule': sched(r.get('energyweekendschedule')),
        'uri': r.get('uri') or ('https://apps.openei.org/USURDB/rate/view/' + r['label'] if r.get('label') else ''),
    }


def plan_ok(p, now):
    if p['enddate'] and p['enddate'] <= now:
        return False
    if not p['energyratestructure'] or not any(p['energyratestructure']):
        return False
    n = len(p['energyratestructure'])
    for s in (p['energyweekdayschedule'], p['energyweekendschedule']):
        if len(s) != 12 or any(h >= n or h < 0 for m in s for h in m):
            return False
    return all(row for row in p['energyratestructure'])


def is_tou(p):
    return len({h for m in p['energyweekdayschedule'] + p['energyweekendschedule'] for h in m}) > 1


def build_plans(rows):
    keys = list(rows[0].keys()) if rows else []
    print('URDB columns: %d; rate columns: %d' % (len(keys), sum(1 for k in keys if COL.match(k))))
    now = time.time()
    by = {}
    for r in rows:
        if (r.get('sector') or '').strip().lower() != 'residential':
            continue
        if str(r.get('approved', 'true')).strip().lower() in ('false', '0', 'no'):
            continue
        try:
            p = trim(r, keys)
        except (ValueError, KeyError):
            continue
        if not p['eiaid'] or not plan_ok(p, now):
            continue
        by.setdefault(p['eiaid'], []).append(p)
    out = {}
    for eid, plans in by.items():
        plans.sort(key=lambda p: p['startdate'] or 0, reverse=True)
        seen, keep = set(), []
        for p in plans:  # newest version of each plan name
            k = re.sub(r'\s+', ' ', p['name'].lower())
            if k in seen:
                continue
            seen.add(k)
            keep.append(p)
        keep.sort(key=lambda p: (not is_tou(p), not re.search(r'\bev\b|electric vehicle', p['name'], re.I), -(p['startdate'] or 0)))
        out[eid] = keep[:MAX_PLANS]
    return out


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, separators=(',', ':'), ensure_ascii=False)


def main(argv):
    zip_files, urdb_file = [], None
    if '--zip' in argv:
        i = argv.index('--zip') + 1
        while i < len(argv) and not argv[i].startswith('--'):
            zip_files.append(argv[i]); i += 1
    if '--urdb' in argv:
        urdb_file = argv[argv.index('--urdb') + 1]

    zip_rows, zip_src = [], []
    if zip_files:
        for f in zip_files:
            zip_rows += read_csv_bytes(open(f, 'rb').read(), f); zip_src.append(os.path.basename(f))
    else:
        for u in discover_zip_csvs():
            zip_rows += read_csv_bytes(fetch(u), u); zip_src.append(u)
    if urdb_file:
        urdb_rows = read_csv_bytes(open(urdb_file, 'rb').read(), urdb_file); urdb_src = os.path.basename(urdb_file)
    else:
        u = discover_urdb(); urdb_rows = read_csv_bytes(fetch(u), u); urdb_src = u
    print('ZIP rows: %d, URDB rows: %d' % (len(zip_rows), len(urdb_rows)))

    zips, util = build_zip_map(zip_rows)
    plans = build_plans(urdb_rows)
    if len(zips) < 1000 and not zip_files:
        raise SystemExit('ZIP map looks too small (%d); not writing' % len(zips))

    tmp = OUT + '.tmp'
    shutil.rmtree(tmp, ignore_errors=True)
    shards = {}
    for z, ids in zips.items():
        shards.setdefault(z[:3], {})[z] = ids
    for pre, m in shards.items():
        write(os.path.join(tmp, 'zip', pre + '.json'), m)
    with_plans = 0
    for eid, u in util.items():
        items = plans.get(eid, [])
        with_plans += bool(items)
        write(os.path.join(tmp, 'u', '%d.json' % eid), {'eiaid': eid, 'utility': u['utility'], 'state': u['state'], 'res': u['res'], 'items': items})
    meta = {'built': datetime.date.today().isoformat(), 'zips': len(zips), 'utilities': len(util), 'utilitiesWithPlans': with_plans,
            'sources': {'zip': {'name': 'EIA Form 861 via OpenEI: U.S. Electric Utility Companies and Rates, Look-up by Zip Code', 'files': zip_src, 'license': 'CC BY 4.0'},
                        'plans': {'name': 'OpenEI U.S. Utility Rate Database (URDB)', 'file': urdb_src, 'license': 'CC BY 4.0'}}}
    write(os.path.join(tmp, 'meta.json'), meta)
    shutil.rmtree(OUT, ignore_errors=True)
    os.rename(tmp, OUT)
    print('Wrote %d ZIPs in %d shards, %d utilities (%d with residential plans).' % (len(zips), len(shards), len(util), with_plans))


if __name__ == '__main__':
    main(sys.argv[1:])

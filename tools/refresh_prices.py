#!/usr/bin/env python3
"""
refresh_prices.py

Refreshes data/fuel-prices.json from the U.S. Energy Information Administration API:
  - weekly retail gasoline, regular and premium, for the U.S., its regions, and the states EIA publishes
  - monthly average residential electricity price by state

    EIA_API_KEY=... python3 tools/refresh_prices.py

Free key: https://www.eia.gov/opendata/register.php. Standard library only.
Leaves the file alone (and exits 0) if the key is missing or EIA doesn't answer,
so a bad week never breaks the site. The public fast-charging price is edited by hand.
"""
import json, os, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'data', 'fuel-prices.json')
API = 'https://api.eia.gov/v2/'
AREAS = ['NUS', 'R10', 'R1X', 'R1Y', 'R1Z', 'R20', 'R30', 'R40', 'R50', 'R5XCA',
         'SCA', 'SCO', 'SFL', 'SMA', 'SMN', 'SNY', 'SOH', 'STX', 'SWA']
STATES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())


def get(route, params):
    q = [('api_key', os.environ['EIA_API_KEY'])] + params
    url = API + route + '?' + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)['response']['data']


def gasoline(d):
    params = [('frequency', 'weekly'), ('data[0]', 'value'), ('facets[process][]', 'PTE'),
              ('facets[product][]', 'EPMR'), ('facets[product][]', 'EPMP'),
              ('sort[0][column]', 'period'), ('sort[0][direction]', 'desc'), ('length', '400')]
    params += [('facets[duoarea][]', a) for a in AREAS]
    rows = get('petroleum/pri/gnd/data/', params)
    if not rows:
        return False
    week = max(r['period'] for r in rows)
    got = 0
    for r in rows:
        if r['period'] != week or r.get('value') in (None, ''):
            continue
        a = d['gasoline']['areas'].get(r['duoarea'])
        if not a:
            continue
        a['regular' if r['product'] == 'EPMR' else 'premium'] = round(float(r['value']), 3)
        got += 1
    if got < 10:
        return False
    d['gasoline']['week'] = week
    d['gasoline'].pop('premiumNote', None)
    print('gasoline: %s, %d prices' % (week, got))
    return True


def electricity(d):
    params = [('frequency', 'monthly'), ('data[0]', 'price'), ('facets[sectorid][]', 'RES'),
              ('sort[0][column]', 'period'), ('sort[0][direction]', 'desc'), ('length', '300')]
    rows = get('electricity/retail-sales/data/', params)
    if not rows:
        return False
    month = max(r['period'] for r in rows)
    latest = {r['stateid']: float(r['price']) for r in rows if r['period'] == month and r.get('price') not in (None, '')}
    states = {k: round(v, 2) for k, v in latest.items() if k in STATES}
    if len(states) < 45:
        return False
    d['electricity']['states'] = states
    d['electricity']['month'] = month
    if 'US' in latest:
        d['electricity']['us'] = round(latest['US'], 2)
        d['electricity']['usMonth'] = month
    print('electricity: %s, %d states' % (month, len(states)))
    return True


def main():
    if not os.environ.get('EIA_API_KEY'):
        print('No EIA_API_KEY; leaving data/fuel-prices.json as is.')
        return
    d = json.load(open(PATH, encoding='utf-8'))
    changed = False
    for fn in (gasoline, electricity):
        try:
            changed = fn(d) or changed
        except Exception as e:  # keep last week's numbers rather than fail the build
            print('%s: %s' % (fn.__name__, e), file=sys.stderr)
    if changed:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=1)
            f.write('\n')


if __name__ == '__main__':
    main()

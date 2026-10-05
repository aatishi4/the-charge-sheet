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
HOME_PUBLISHED = '2026-09-30'  # the home side went live

# view id, URL slug ('' is home), page title, meta description, kind
PAGES = [
    ('home', '', 'EV Charging, Explained: Free Guides and Calculators',
     'A free, honest guide to EV charging: how it works, what it costs at home or as a business, and how to get it right. Real data and free tools.', 'home'),
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
    ('software', 'ev-charging-software-ocpp', 'EV Charging Software and OCPP: Choosing a Backend',
     'What charging software does, what OCPP is and is not, what a backend costs and who pays, free vs premium platforms, payments, maps, and support.', 'guide'),
    ('vendors', 'buying-ev-chargers', 'Buying EV Chargers: Vendor Questions and Red Flags',
     'What to ask charger vendors, installers, and software providers, what a good answer sounds like, and the walk-away signs. For site hosts and operators.', 'guide'),
    ('fleet', 'fleet-ev-charging', 'Fleet EV Charging: Throughput, Power, and Operations',
     'Fleet charging is a logistics problem. How to plan for throughput, the 80% rule, site power, charge windows, and the operations that make or break a depot.', 'guide'),
    ('benchmarks', 'ev-charging-benchmarks', 'EV Charging Benchmarks: Real Utilization Data',
     'Sessions per day, energy per session, and utilization from operating US charging sites. Session-level data, anonymized, with nothing modeled or rounded up.', 'guide'),
    ('method', 'methodology', 'Method and Sources: How The Charge Sheet Works',
     'Every formula behind the forecast, site planner, and battery math, where the benchmark data comes from, and the limits of each.', 'guide'),
    ('glossary', 'ev-charging-glossary', 'EV Charging Glossary: Plain-English Terms, Home and Business',
     'Demand charges, OCPP, time of use, V2H, NEMA 14-50, DSCR and the rest of the EV charging jargon, in plain English for homeowners and site owners.', 'glossary'),
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
    ('hardware', 'ev-chargers', 'DC Fast and Level 2 EV Chargers: Specs and Datasheets',
     'DC fast and Level 2 chargers with specs from the manufacturer datasheet: power, ports, output tables and certifications. Load any of them into the site planner.', 'tool'),
    ('report', 'ev-charging-project-report', 'EV Charging Project Report: One PDF for Your Whole Plan',
     'Save results from the site planner, install estimator, SBA loan check, fleet calculator, forecast and signal check, then export one PDF for your project.', 'tool'),
    ('work', 'work-with-me', 'Work With Aatish Patel on Your EV Charging Project',
     'Planning chargers for a dealership, hotel, fleet depot or other site? Tell Aatish Patel about it and get a straight answer from someone who has run them.', 'contact'),
    ('about', 'about', 'About The Charge Sheet and Aatish Patel',
     'Who wrote The Charge Sheet and why: lessons from building an EV charging company, written down so you can skip learning them the expensive way.', 'about'),
]
# The home side (residential charging, batteries, V2H). Built into previews always; on chargesheet.io only once
# HOME_LIVE is True. Until then everything between <!--home-side--> markers in index.html is stripped from the
# production build, and preview pages carry noindex and stay out of the sitemap.
HOME_LIVE = True
HOME_ON = HOME_LIVE or os.environ.get('CF_PAGES_BRANCH', 'main') != 'main' or os.environ.get('SHOW_HOME') == '1'
HOME_PAGES = [
    ('hhub', 'home', 'Home EV Charging, Home Batteries and V2H: The Charge Sheet',
     'Charging an EV at home, what your panel can take, time-of-use rates, home batteries, and cars that can power the house. Free guides and calculators.', 'guide'),
    ('hbasics', 'home/ev-charging-at-home', 'Home EV Charging: Level 1 vs Level 2, Plug-In vs Hardwired',
     'Level 1 or Level 2, 32 or 48 amps, a NEMA 14-50 or hardwired, a mobile cord or a wall box. What home EV charging needs and what it gets wrong.', 'guide'),
    ('hcost', 'home/home-ev-charging-cost', 'How Much Does It Cost to Charge an EV at Home?',
     'The math behind home charging costs, time-of-use and EV rate plans, the 4pm trap, and how home charging compares with gas and public fast charging.', 'guide'),
    ('hbattery', 'home/home-battery-backup', 'Home Battery Backup: What It Does and What It Costs',
     'Backup power, time shifting and solar storage. kW versus kWh, surge and air conditioners, whole-home versus essentials, 2026 prices and tax credits.', 'guide'),
    ('hvtoh', 'home/vehicle-to-home-v2h', 'Vehicle-to-Home (V2H): Which EVs Can Power a House',
     'Which EVs can run a house today, the hardware in between, what it costs, and the pros and cons of using your car as a home battery.', 'guide'),
    ('hrent', 'home/ev-charging-apartment-condo-hoa', 'EV Charging in an Apartment, Condo or HOA: Your Rights',
     'Right-to-charge laws by state, your options from a plain outlet to shared chargers, who pays for the power, and a letter to send your board or landlord.', 'guide'),
    ('hroad', 'home/ev-road-trip-charging', 'EV Road Trip Charging: Stops, Etiquette and the 80% Rule',
     'How many charging stops a road trip takes, why 80% beats 100% at a fast charger, what it costs, plugs and adapters, and charging etiquette.', 'guide'),
    ('hquote', 'home/hiring-electrician-ev-charger', 'Hiring an Electrician for an EV Charger: Quote Checklist',
     'Who to hire for a home EV charger, what a proper quote includes, breaker sizes, permits and red flags. Check your own quote line by line.', 'guide'),
    ('hstart', 'home/start', 'What Home EV Charger Do I Need? A Two-Minute Answer',
     'Your car, your commute, where you park and your panel. Get the setup to install, what it costs, rebates from your utility, and what to ask the electrician.', 'tool'),
    ('hcharge', 'home/ev-charging-cost-calculator', 'Home EV Charging Cost Calculator with Time-of-Use Rates',
     'Your car, your arrival charge, your plug-in time and your utility rate. Finds the cheapest charging hours and the cost per night, month and year.', 'tool'),
    ('hinstall', 'home/home-ev-charger-installation-cost', 'Home EV Charger Installation Cost and Panel Load Calculator',
     'Estimate a home charger install from panel size, free spaces, breaker, distance and route. Checks the NEC 220.83 load and prices the fixes if it does not fit.', 'tool'),
    ('hrebates', 'home/ev-charger-rebates', 'Home EV Charger Rebates by ZIP Code (2026)',
     'Charger rebates, EV electricity rates and car incentives from your utility and state, looked up by ZIP code from the DOE database and refreshed weekly.', 'tool'),
    ('hbackup', 'home/home-battery-backup-calculator', 'Home Battery Backup Calculator: Size a Battery for an Outage',
     'Pick what stays on in an outage. Get running power, start-up surge and energy, then see which home batteries cover it and how many you need.', 'tool'),
    ('hvcompare', 'home/v2h-vs-home-battery', 'V2H vs Home Battery: Can Your EV Replace a Powerwall?',
     'Compare a bidirectional EV with a home battery for backup: usable energy, power, days of backup, cost, and the trade-offs.', 'tool'),
    ('hadapt', 'home/ev-charging-adapter-finder', 'EV Charging Adapter Finder: NACS, CCS1 and J1772',
     'Pick your EV and see which chargers it plugs straight into, which adapter the rest need (Supercharger, CCS, Level 2) and what each adapter costs.', 'tool'),
    ('hgear', 'home/home-ev-chargers-batteries', 'Home EV Chargers, Home Batteries and Bidirectional EVs',
     'Home Level 2 chargers, home batteries and every US EV that can send power out, with specs, prices and honest notes on what works today.', 'tool'),
]
HOME_IDS = [p[0] for p in HOME_PAGES]
GEAR_TAG = ['']  # filled in build(); only the home pages carry the gear data
GEAR_TAGS = {}   # per home page: the gear data minus the big lists that page doesn't use
GEAR_OPTIONAL = ('ports', 'adapters', 'panel', 'rtc')
GEAR_EXTRA = {'hgear': ('adapters', 'panel'), 'hadapt': ('ports', 'adapters'), 'hstart': ('panel', 'rtc'),
              'hrent': ('rtc',), 'hrebates': ('rtc',), 'hinstall': ('panel',)}
PRODUCTS_TAG = ['']  # filled in build(); only the pages that use the charger catalog carry it
PRODUCT_VIEWS = ('planner', 'hardware', 'report')
PRODUCT_PAGES = []  # (url, name, description), filled in build(); used by llms.txt
GEAR_PAGES = []
if HOME_ON:
    PAGES = PAGES + HOME_PAGES
VIEWS = [p[0] for p in PAGES]
PATH = {p[0]: ('/' + p[1] + '/' if p[1] else '/') for p in PAGES}


def section_dates(src, fallback):
    """Date each page's section last changed, from the git history of index.html, so the sitemap's
    lastmod and dateModified move only when that page's own content does. Falls back to the last
    commit date when history is unavailable (e.g. a shallow clone)."""
    def hashes(text):
        try:
            return {v: hashlib.sha1(text[a:b].encode('utf-8')).hexdigest() for v, a, b in section_bounds(text)}
        except Exception:
            return {}
    dates = {}
    try:
        # Cloudflare Pages builds from a shallow clone; fetch the history once so the dates are real.
        shallow = subprocess.run(['git', 'rev-parse', '--is-shallow-repository'], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        if shallow == 'true':
            r = subprocess.run(['git', 'fetch', '--quiet', '--deepen=200'], cwd=ROOT, capture_output=True, text=True, timeout=90)
            print('Git history for sitemap dates: %s' % ('fetched' if r.returncode == 0 else 'unavailable (%s)' % r.stderr.strip()[:120]))
        log = subprocess.run(['git', 'log', '--format=%H %cs', '-n', '80', '--', 'index.html'], cwd=ROOT,
                             capture_output=True, text=True, timeout=20).stdout.split('\n')
        revs = [l.split() for l in log if l.strip()][::-1]  # oldest first
        prev = {}
        for rev, day in revs:
            old = subprocess.run(['git', 'show', rev + ':index.html'], cwd=ROOT, capture_output=True, text=True, timeout=20).stdout
            for v, h in hashes(old).items():
                if prev.get(v) != h:
                    dates[v] = day
                    prev[v] = h
        for v, h in hashes(src).items():  # uncommitted edits in a local build
            if prev and prev.get(v) != h:
                dates[v] = datetime.date.today().isoformat()
    except Exception:
        pass
    return {v: dates.get(v, fallback) for v in VIEWS}


STATE_NAMES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
               'DE': 'Delaware', 'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois',
               'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
               'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana',
               'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
               'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
               'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
               'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'}


def prerender_catalogs(full):
    """The charger catalog and the home gear page are drawn by the script. Put a plain list of the same
    products in the HTML so crawlers (and anyone without JS) see real content; the script replaces it."""
    try:
        prods = json.load(open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8'))
    except Exception:
        prods = []
    if prods and 'hardware' in full:
        def plist(items):
            return '<ul>%s</ul>' % ''.join(
                '<li><a href="/ev-chargers/%s/"><b>%s %s</b></a>: %s, up to %s kW, %s port%s. %s</li>' % (
                    esc(p['id']), esc(p['oem']), esc(p['model']), esc(p.get('kind', '')), esc(str(p.get('maxKw', ''))),
                    esc(str(p.get('ports', ''))), '' if str(p.get('ports')) == '1' else 's', esc(p.get('blurb', '')))
                for p in items)
        dc = [p for p in prods if p.get('type') != 'l2']
        l2 = [p for p in prods if p.get('type') == 'l2']
        body = ('<div class="wrap prose">' + ('<h2>DC fast chargers</h2>' + plist(dc) if dc else '') +
                ('<h2>Level 2 chargers</h2>' + plist(l2) if l2 else '') + '</div>')
        full['hardware'] = full['hardware'].replace('<div class="hw" id="hw-body"></div>', '<div class="hw" id="hw-body">%s</div>' % body, 1)
    if 'hgear' in full:
        try:
            g = json.load(open(os.path.join(ROOT, 'data', 'home-gear.json'), encoding='utf-8'))
        except Exception:
            return
        ch = ''.join('<li><a href="/home/home-ev-chargers-batteries/%s/"><b>%s %s</b></a>: %s, %s A, %s. %s</li>' % (esc(c['id']), esc(c['oem']), esc(c['model']), esc(c.get('kind', '')), esc(str(c.get('amps', ''))),
                     esc(c.get('connector', '')), esc(c.get('blurb', ''))) for c in g.get('chargers', []))
        ba = ''.join('<li><a href="/home/home-ev-chargers-batteries/%s/"><b>%s %s</b></a>: %s kWh, %s kW continuous. %s</li>' % (esc(b['id']), esc(b['oem']), esc(b['model']), esc(str(b.get('kwh', ''))),
                     esc(str(b.get('kw', ''))), esc(b.get('blurb', ''))) for b in g.get('batteries', []))
        v2h = {'yes': 'V2H today', 'legacy': 'V2H on older hardware', 'announced': 'V2H announced'}
        ve = ''.join('<li><a href="/home/home-ev-chargers-batteries/%s/"><b>%s %s</b></a> (%s): %s kWh battery%s%s.</li>' % (esc(v['id']), esc(v['make']), esc(v['model']), esc(str(v.get('years', ''))), esc(str(v.get('kwh', ''))),
                     ', V2L' if str(v.get('v2l', '0')) not in ('0', '', 'None') else '', (', ' + v2h[v['v2h']]) if v.get('v2h') in v2h else '')
                     for v in g.get('vehicles', []) if str(v.get('v2l', '0')) not in ('0', '', 'None') or v.get('v2h') in v2h)
        pa = ''.join('<li><a href="/home/home-ev-chargers-batteries/%s/"><b>%s %s</b></a>: %s. %s</li>' % (esc(x['id']), esc(x['oem']), esc(x['model']), esc(x.get('kind', '')), esc(x.get('blurb', '')))
                     for x in g.get('panel', []))
        ad = ''.join('<li><a href="/home/home-ev-chargers-batteries/%s/"><b>%s %s</b></a> (%s): %s</li>' % (esc(x['id']), esc(x['maker']), esc(x['name']), esc(x.get('dir', '').replace('-to-', ' to ')), esc(x.get('who', '')))
                     for x in g.get('adapters', []))
        body = ('<div class="prose">' + ('<h2>Home EV chargers</h2><ul>%s</ul>' % ch if ch else '') +
                ('<h2>Home batteries</h2><ul>%s</ul>' % ba if ba else '') +
                ('<h2>EVs that can send power out</h2><ul>%s</ul>' % ve if ve else '') +
                ('<h2>Panel helpers: load managers, splitters and smart panels</h2><ul>%s</ul>' % pa if pa else '') +
                ('<h2>Charging adapters</h2><ul>%s</ul>' % ad if ad else '') + '</div>')
        full['hgear'] = full['hgear'].replace('<div class="wrap hgear" id="h-gear"></div>', '<div class="wrap hgear" id="h-gear">%s</div>' % body, 1)
        if 'hrent' in full and g.get('rtc'):
            names = dict((k, v) for k, v in STATE_NAMES.items())
            rows = ''.join('<tr><th>%s</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(names.get(r['st'], r['st'])), esc(r['hoa']), esc(r['renters']), esc(r['cites']))
                           for r in g['rtc'])
            table = ('<div class="scroll" tabindex="0"><table class="hrtc-t"><thead><tr><th>State</th><th>Condos and HOAs</th><th>Renters</th><th>Law</th></tr></thead>'
                     '<tbody>%s</tbody></table></div>' % rows)
            full['hrent'] = full['hrent'].replace('<div id="h-rtc-all"></div>', '<div id="h-rtc-all">%s</div>' % table, 1)
    if 'hrebates' in full:
        inc_dir = os.path.join(ROOT, 'data', 'incentives')
        parts = []
        for st in sorted(STATE_NAMES, key=lambda k: STATE_NAMES[k]):
            try:
                d = json.load(open(os.path.join(inc_dir, st + '.json'), encoding='utf-8'))
            except Exception:
                continue
            chg = [u['name'] for u in d.get('utils', []) if u.get('res', {}).get('Infrastructure')]
            rate = [u['name'] for u in d.get('utils', []) if u.get('res', {}).get('Fuel Prices')]
            sp = [r['title'] for r in d.get('state', []) if r.get('kind') == 'charger']
            if not (chg or rate or sp):
                parts.append('<li><b>%s</b>: no home charger programs in the DOE database right now.</li>' % esc(STATE_NAMES[st]))
                continue
            bits = []
            if chg:
                bits.append('home charger programs from %s' % esc(', '.join(chg)))
            if rate:
                bits.append('EV or time-of-use rates from %s' % esc(', '.join(rate)))
            if sp:
                bits.append('state programs: %s' % esc('; '.join(sp)))
            parts.append('<li><b>%s</b>: %s.</li>' % (esc(STATE_NAMES[st]), '; '.join(bits)))
        if parts:
            body = ('<h2 id="h-rb-states">Every state, at a glance</h2><p>Utilities and state programs with home charging incentives, from the '
                    'Department of Energy\u2019s database. Type your ZIP code above for the details and links.</p><ul class="hreb-all">%s</ul>' % ''.join(parts))
            full['hrebates'] = full['hrebates'].replace('<div class="wrap prose" id="h-reb-all"></div>', '<div class="wrap prose" id="h-reb-all">%s</div>' % body, 1)


def write_llms_txt(h1s):
    """dist/llms.txt (llmstxt.org): a plain map of the site for AI search tools, built from PAGES."""
    groups = [('Business guides', lambda v, k: k == 'guide' and v not in HOME_IDS),
              ('Business tools', lambda v, k: k == 'tool' and v not in HOME_IDS),
              ('At home: guides', lambda v, k: k == 'guide' and v in HOME_IDS),
              ('At home: tools', lambda v, k: k == 'tool' and v in HOME_IDS),
              ('About', lambda v, k: k in ('about', 'contact', 'glossary'))]
    out = ['# %s' % SITE_NAME, '',
           '> A free guide to EV charging, at home and in business: how charging works, what it costs, '
           'and how to plan it, with calculators and real data. Written by Aatish Patel, who built and ran '
           'a charging company. Every formula is on the methodology page.', '']
    for name, test in groups:
        rows = [p for p in PAGES if test(p[0], p[4])]
        if not rows:
            continue
        out += ['## ' + name, '']
        out += ['- [%s](%s%s): %s' % (h1s.get(v) or t, SITE, PATH[v], d) for v, _, t, d, _ in rows]
        out.append('')
    if PRODUCT_PAGES:
        out += ['## Chargers', ''] + ['- [%s](%s): %s' % (n, u, d) for u, n, d in PRODUCT_PAGES] + ['']
    if GEAR_PAGES:
        out += ['## Home gear', ''] + ['- [%s](%s): %s' % (n, u, d) for u, n, d in GEAR_PAGES] + ['']
    out += ['## Optional', '', '- [Blog](%s/blog/): notes on the business of EV charging.' % SITE,
            '- [Source code](https://github.com/aatishi4/the-charge-sheet): the whole site, open source.', '']
    open(os.path.join(OUT, 'llms.txt'), 'w', encoding='utf-8').write('\n'.join(out))


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
    if n.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        # an empty heading in a hidden section is still a heading to a crawler; keep the element, drop the rank
        n.raw = re.sub(r'^<\s*h[1-6]', '<div data-h="%s"' % n.tag[1], n.raw)
    if n.tag == 'a':
        # empty links to other pages' anchors: keep the element, drop the link
        n.raw = re.sub(r'\shref="[^"]*"', '', re.sub(r'^<\s*a\b', '<span data-a', n.raw))
    for c in n.children:
        hollow(c)


def keep(n):
    """Prune a hollowed tree to what the script can address: elements with an id or a data-
    attribute, and their ancestors. Everything else in a view nobody sees is dead weight."""
    n.children = [c for c in n.children if c.text is None and keep(c)]
    if n.tag in HOOK_TAGS:
        return True
    return bool(n.children) or 'id' in n.attrs or any(k.startswith('data-') for k in n.attrs)


def hollow_html(fragment):
    root = parse(fragment)
    root.children = [c for c in root.children if c.text is None]
    for c in root.children:
        hollow(c)
        keep(c)
    return root.html()


# ---------- helpers ----------
def esc(s):
    return html.escape(s, quote=True)


def absolutize_srcset(s):
    """Every candidate in a srcset, not just the first (the attribute rule below only sees the start)."""
    def fix(m):
        parts = [c.strip() for c in m.group(2).split(',')]
        parts = [re.sub(r'^(?:\./)?((?:img|og)/)', r'/\1', c) for c in parts]
        return m.group(1) + ', '.join(parts) + '"'
    return re.sub(r'(srcset=")([^"]*)"', fix, s)


def absolutize_html(s):
    s = absolutize_srcset(s)
    return re.sub(r'((?:href|src|srcset|poster)=")(?:\./)?((?:fonts|img|data|og)/[^"]*|favicon[^"]*|apple-touch-icon\.png|og-image\.png)"', r'\1/\2"', s)


def absolutize_css(s):
    return re.sub(r'url\((["\']?)(?:\./)?(?!data:|https?:|/|#)', r'url(\1/', s)


def absolutize_js(s):
    return re.sub(r'([\'"])(?:\./)?(img|data|fonts|og)/', r'\1/\2/', s)


JS_PATHS = {}
GROUPS = {}  # view -> (group title, [(view, label)]), read from the GROUPS table in the app script
NAV_OF = {}  # view -> id of its top-nav link (gn-learn, gn-tools, ...)


def read_groups(src):
    m = re.search(r'var GROUPS = \{(.*?)\n\s*\};', src, re.S)
    if not m:
        return
    for g, title, nav, pages in re.findall(r"(\w+):\s*\{title:'([^']+)',\s*nav:'([^']+)',\s*pages:\[(.*?)\]\}", m.group(1)):
        items = re.findall(r"\['(\w+)','([^']+)'\]", pages)
        for v, _ in items:
            GROUPS[v] = (title, items)
            NAV_OF[v] = nav


def fill_snav(pm, v):
    """Draw the section sub-nav in the HTML (the script used to add it after load, which shifted the page).
    Also mark the current top-nav link and Business/Home pill, so they are right on first paint
    (the page transition captures them before the script runs)."""
    nav = NAV_OF.get(v) or ('gn-about' if v == 'about' else None)
    if nav:
        pm = pm.replace('id="%s"' % nav, 'id="%s" aria-current="true"' % nav, 1)
    side = 'home' if v in HOME_IDS else ('biz' if (v in GROUPS or v == 'home') else None)
    if side:
        on, off = ('sw-home', 'sw-biz') if side == 'home' else ('sw-biz', 'sw-home')
        pm = pm.replace('<a class="%s" ' % on, '<a class="%s" aria-current="true" ' % on).replace('<a class="%s" ' % off, '<a class="%s" aria-current="false" ' % off)
    if v not in GROUPS:
        return pm
    title, items = GROUPS[v]
    links = ''.join('<a href="%s"%s>%s</a>' % (PATH[x], ' aria-current="page"' if x == v else '', esc(label))
                    for x, label in items if x in PATH)
    pm = pm.replace('<div class="snav" id="snav" hidden>', '<div class="snav" id="snav">', 1)
    pm = pm.replace('<span class="snav-t" id="snav-t"></span>', '<span class="snav-t" id="snav-t">%s</span>' % esc(title), 1)
    return pm.replace('<nav class="snav-links" id="snav-links" aria-label="In this section"></nav>',
                      '<nav class="snav-links" id="snav-links" aria-label="In this section">%s</nav>' % links, 1)



def minify_js(code):
    """Strip comments and whitespace with rjsmin (vendored, Apache 2.0). Falls back to the source."""
    if code in MINIFIED:
        return MINIFIED[code]
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor'))
        import rjsmin
        out = rjsmin.jsmin(code)
    except Exception as e:  # never fail the build over minification
        print('JS minification skipped: %s' % e)
        out = code
    MINIFIED[code] = out
    return out


MINIFIED = {}


def point_scripts():
    """Every built page gets the business bundle, except /home/ pages, which get the full one."""
    for dirpath, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith('.html'):
                continue
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, OUT).replace(os.sep, '/')
            doc = open(path, encoding='utf-8').read()
            if '%%JS%%' in doc:
                doc = doc.replace('%%JS%%', JS_PATHS['home' if rel.startswith('home/') else 'biz'])
                open(path, 'w', encoding='utf-8').write(doc)


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
    sub(r'<meta property="og:type" content="[^"]*">', '<meta property="og:type" content="%s">' % ('website' if kind in ('home', 'tool', 'about', 'glossary', 'contact') else 'article'))
    sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url)
    sub(r'<meta property="og:image" content="[^"]*">', '<meta property="og:image" content="%s">\n<meta property="og:image:alt" content="%s">' % (image, esc(title)))
    sub(r'<meta name="twitter:image" content="[^"]*">', '<meta name="twitter:image" content="%s">\n<meta name="twitter:title" content="%s">\n<meta name="twitter:description" content="%s">' % (image, esc(title), esc(desc)))
    sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">\n<meta name="robots" content="index, follow, max-image-preview:large">' % url)
    return head


GLOSSARY = []


def jsonld(title, desc, url, image, kind, h1, updated, v=None):
    graph = []
    home_side = v in HOME_IDS
    if home_side:
        updated = max(updated, HOME_PUBLISHED)
    author_ref = {'@id': SITE + '/#author'}
    if kind == 'home':
        graph.append({'@type': 'WebSite', '@id': SITE + '/#website', 'name': SITE_NAME, 'url': SITE + '/',
                      'description': desc, 'inLanguage': 'en-US', 'publisher': author_ref})
        graph.append(dict(AUTHOR, **{'@id': SITE + '/#author'}))
    elif kind == 'about':
        graph.append({'@type': 'ProfilePage', 'url': url, 'name': title, 'dateModified': updated,
                      'mainEntity': dict(AUTHOR, **{'@id': SITE + '/#author'})})
    elif kind == 'contact':
        graph.append({'@type': 'ContactPage', 'url': url, 'name': h1 or title, 'description': desc, 'dateModified': updated,
                      'about': dict(AUTHOR, **{'@id': SITE + '/#author'})})
    elif kind == 'glossary':
        graph.append({'@type': 'DefinedTermSet', '@id': url + '#terms', 'name': h1 or title, 'url': url, 'description': desc,
                      'hasDefinedTerm': [{'@type': 'DefinedTerm', 'name': t, 'description': dd, 'url': url + '#g-' + gid}
                                         for gid, t, dd in (GLOSSARY or [])]})
    elif v == 'hhub':
        graph.append({'@type': 'CollectionPage', 'name': h1 or title, 'headline': title, 'description': desc, 'url': url,
                      'image': image, 'inLanguage': 'en-US', 'datePublished': HOME_PUBLISHED, 'dateModified': updated,
                      'author': dict(AUTHOR), 'isPartOf': {'@type': 'WebSite', 'name': SITE_NAME, 'url': SITE + '/'},
                      'hasPart': [{'@type': 'WebPage', 'name': p[2], 'url': SITE + PATH[p[0]]} for p in HOME_PAGES if p[0] != 'hhub']})
    elif kind == 'tool':
        graph.append({'@type': 'WebApplication', 'name': h1 or title, 'url': url, 'description': desc,
                      'applicationCategory': 'UtilitiesApplication' if home_side else 'BusinessApplication', 'operatingSystem': 'Any', 'isAccessibleForFree': True,
                      'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
                      'author': dict(AUTHOR), 'image': image})
    else:
        graph.append({'@type': 'Article', 'headline': title, 'name': h1 or title, 'description': desc, 'url': url,
                      'mainEntityOfPage': url, 'image': image, 'inLanguage': 'en-US',
                      'datePublished': HOME_PUBLISHED if home_side else PUBLISHED, 'dateModified': updated,
                      'author': dict(AUTHOR), 'publisher': dict(AUTHOR),
                      'isPartOf': {'@type': 'WebSite', 'name': SITE_NAME, 'url': SITE + '/'}})
    if kind != 'home':
        crumbs = [(SITE_NAME, SITE + '/')]
        if home_side and v != 'hhub':
            crumbs.append(('At home', SITE + '/home/'))
        crumbs.append(('At home' if v == 'hhub' else (h1 or title), url))
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]})
    data = {'@context': 'https://schema.org', '@graph': graph}
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(data, ensure_ascii=False).replace('</', '<\\/')


def config_script(page, anchors, product=None):
    return '<script>window.CS_PAGE=%s;window.CS_PATHS=%s;window.CS_ANCHORS=%s;window.CS_HOME_LIVE=%s;%s</script>\n' % (
        json.dumps(page), json.dumps(PATH), json.dumps(anchors), 'true' if HOME_LIVE else 'false',
        ('window.CS_PRODUCT=%s;' % json.dumps(product)) if product else '')


def load_products():
    try:
        return json.load(open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8'))
    except Exception:
        return []


def product_title(p):
    oem = p['oem'].replace(' North America', '')
    kind = 'Level 2 Charger' if p.get('type') == 'l2' else 'DC Fast Charger'
    t = '%s %s %s: Specs and Datasheet' % (oem, p['model'], kind)
    return t if len(t) <= 60 else '%s %s: Specs and Datasheet' % (oem, p['model'])


def product_desc(p):
    lead = '%s %s: %s, up to %s kW%s, %s port%s.' % (p['oem'], p['model'], p.get('kind', ''), p.get('maxKw', ''),
                                                     ' per port' if p.get('type') == 'l2' else '', p.get('ports', ''),
                                                     '' if str(p.get('ports')) == '1' else 's')
    d = lead + ' Specs, output settings and certifications from the manufacturer datasheet.'
    return d if len(d) <= 160 else lead


V2H_LABEL = {'yes': 'Can run a house today', 'legacy': 'Discontinued, existing owners only',
             'announced': 'Announced, not shipping', 'no': 'No V2H in the US'}


def usd(v):
    try:
        return '$' + format(int(round(float(v))), ',')
    except (TypeError, ValueError):
        return ''


def fit60(*options):
    for t in options:
        if len(t) <= 60:
            return t
    return options[-1]


def gear_items(g):
    return [(k, x) for k in ('chargers', 'batteries', 'vehicles', 'panel', 'adapters') for x in g.get(k, [])]


def gear_meta(kind, x):
    """(name, title, description) for a home gear page."""
    if kind == 'vehicles':
        name = '%s %s' % (x['make'], x['model'])
        title = fit60('%s: Can It Power a House? V2H and V2L' % name, '%s: V2H and V2L' % name, name)
        v2l = ('%s kW from its outlets' % x['v2l']) if x.get('v2l') else 'no factory outlets'
        d = '%s (%s): %s, %s. About %s kWh battery, %s kW onboard charger.' % (
            name, x.get('years', ''), {'yes': 'can run a house today', 'legacy': 'V2H discontinued, existing owners only', 'announced': 'V2H announced, not shipping', 'no': 'no V2H in the US'}.get(x.get('v2h'), 'V2H unknown'), v2l, x.get('kwh', ''), x.get('obc', ''))
    elif kind == 'panel':
        name = '%s %s' % (x['oem'], x['model'])
        title = fit60('%s: %s for a Full Panel' % (name, x.get('kind', 'Load manager')), '%s: Price and Specs' % name, name)
        d = '%s, %s: %s %s' % (name, x.get('kind', '').lower(), x.get('how', ''), ('About %s.' % usd(x['price'])) if x.get('price') else '')
    elif kind == 'adapters':
        name = '%s %s' % (x['maker'], x['name'])
        title = fit60('%s: Who Needs It and What It Costs' % name, '%s: Price and Fit' % name, name)
        d = '%s (%s, %s). %s %s' % (name, x.get('dir', '').replace('-to-', ' to '), 'fast charging' if x.get('level') == 'DC' else 'Level 2',
                                    x.get('who', ''), ('About %s.' % usd(x['price'])) if x.get('price') else '')
    elif kind == 'batteries':
        name = '%s %s' % (x['oem'], x['model'])
        title = fit60('%s: Home Battery Specs and Price' % name, '%s: Specs and Price' % name, name)
        d = '%s home battery: %s kWh usable, %s. About %s installed. Specs, surge, warranty and stacking.' % (
            name, x.get('kwh', ''), ('%s kW continuous' % x['kw']) if x.get('kw') else 'no inverter of its own', usd(x.get('price')))
    else:
        name = '%s %s' % (x['oem'], x['model'])
        title = fit60('%s: Home EV Charger Specs and Price' % name, '%s: Specs and Price' % name, name)
        bits = [('%s A' % x['amps']) if x.get('amps') else '', x.get('connector', ''),
                {'hardwire': 'hardwired', 'plug': 'plug-in', 'both': 'plug-in or hardwired', 'cord': 'portable cord'}.get(x.get('install'), '')]
        d = '%s home charger: %s. About %s. Specs, smart features, load management and listing.' % (
            name, ', '.join(b for b in bits if b), usd(x.get('price')))
    if len(d) > 160:
        d = d[:157].rsplit(' ', 1)[0] + '...'
    return name, title, d


def gear_detail_html(kind, x, name):
    """Static gear page body (the script redraws it on load)."""
    if kind in ('panel', 'adapters'):
        if kind == 'panel':
            rows = [('Type', x.get('kind', '')), ('How it works', x.get('how', '')), ('Current', ('Up to %s A' % x['amps']) if x.get('amps') else ''),
                    ('Works with', x.get('worksWith', '')), ('Installation', x.get('installNote', '')), ('Listing', x.get('listing', '')),
                    ('App', x.get('app', '')), ('Price', (('About %s. ' % usd(x['price'])) if x.get('price') else '') + x.get('priceNote', ''))]
            maker, model, blurb, site = x.get('oem', ''), x.get('model', ''), x.get('blurb', ''), x.get('website', '')
        else:
            rows = [('Direction', x.get('dir', '').replace('-to-', ' charger to ') + ' car'), ('Charging', 'DC fast charging' if x.get('level') == 'DC' else 'Level 2 (AC)'),
                    ('Who needs it', x.get('who', '')), ('Listing', x.get('listing', '')),
                    ('Price', ('About %s' % usd(x['price'])) if x.get('price') else ('Free through a dealer' if x.get('price') == 0 else 'Price varies; check the maker'))]
            maker, model, blurb, site = x.get('maker', ''), x.get('name', ''), x.get('who', ''), x.get('url', '')
        table = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (esc(a), esc(str(b))) for a, b in rows if b)
        back = 'panel helpers' if kind == 'panel' else 'adapters'
        pic = ''
        if x.get('img'):
            pic = ('<div class="hgicon has-img"><span class="hgimg %s"><img src="/%s" alt="%s" decoding="async"></span></div>'
                   % ('photo' if x.get('imgFit') == 'photo' else 'cut', esc(x['img']), esc(name)))
        return ('<p class="sub"><a href="/home/home-ev-chargers-batteries/?tab=%s">All %s</a> <span class="dot">/</span> %s</p>'
                '<div class="hwhero hgd">' + pic + '<div><p class="sub">%s</p><h2>%s</h2><p>%s</p>%s</div></div>'
                '<h2>Details</h2><div class="scroll" tabindex="0"><table><tbody>%s</tbody></table></div>'
                '<p class="fh">Source: %s, October 2026.</p>') % (
            kind, back, esc(name), esc(maker), esc(model), esc(blurb),
            ('<p><a class="btn secondary" href="%s" rel="noopener">Maker\u2019s page</a></p>' % esc(site)) if site else '', table,
            ('<a href="%s" rel="noopener">%s</a>' % (esc(x['source']), esc(re.sub(r'^https?://(www\.)?', '', x['source']).split('/')[0]))) if x.get('source') else 'the maker')
    if kind == 'chargers':
        rows = [('Current', ('%s A continuous' % x['amps']) if x.get('amps') else 'Not published'), ('Breaker', ('%s A' % x['breaker']) if x.get('breaker') else ''),
                ('Connects', ({'hardwire': 'Hardwired', 'plug': 'Plug-in', 'both': 'Plug-in or hardwired', 'cord': 'Portable cord'}.get(x.get('install'), '')) + ('. ' + x['plugs'] if x.get('plugs') else '')),
                ('Connector', x.get('connector', '')), ('Export', ('%s kW to the house' % x['exportKw']) if x.get('exportKw') else ''),
                ('Smart features', x.get('smart', '')), ('Load management', x.get('loadMgmt', '')), ('Listing', x.get('listing', '')),
                ('Price', usd(x.get('price')) + (' hardware, before installation' if x.get('bidirectional') else '')), ('Status', x.get('status', ''))]
    elif kind == 'batteries':
        rows = [('Usable energy', '%s kWh' % x.get('kwh', '')), ('Continuous power', ('%s kW' % x['kw']) if x.get('kw') else 'None (adds energy only)'),
                ('Surge', ('%s kW' % x['surgeKw'] + (' (%s)' % x['surgeNote'] if x.get('surgeNote') else '')) if x.get('surgeKw') else 'Not published'),
                ('Chemistry', x.get('chem', '')), ('Coupling', x.get('coupling', '')), ('Stacks up to', '%s units' % x.get('stackMax', '')),
                ('Installed price', 'About %s for the first, %s each after' % (usd(x.get('price')), usd(x.get('addPrice')))), ('Warranty', x.get('warranty', ''))]
    else:
        rows = [('Years', x.get('years', '')), ('Battery', 'About %s kWh' % x.get('kwh', '')), ('Onboard charger', '%s kW AC' % x.get('obc', '')),
                ('Efficiency', 'About %s miles per kWh' % x.get('eff', '')),
                ('V2L', ('%s kW' % x['v2l'] + ('. ' + x['v2lNote'] if x.get('v2lNote') else '')) if x.get('v2l') else 'None from the factory'),
                ('V2H', V2H_LABEL.get(x.get('v2h'), '') + (', up to %s kW' % x['v2hKw'] if x.get('v2hKw') else '')),
                ('Type', x.get('dc', '')), ('V2G', x.get('v2g', '')), ('Export floor', ('%s%%' % x['floor']) if x.get('floor') else '')]
    table = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (esc(a), esc(str(b))) for a, b in rows if b)
    maker = x.get('make') if kind == 'vehicles' else x.get('oem')
    note = x.get('note') if x.get('note') and x.get('blurb') else ''
    pic, cred = '', ''
    if x.get('img'):
        pic = ('<div class="hgicon has-img"><span class="hgimg %s"><img src="/%s" alt="%s" decoding="async"></span></div>'
               % ('photo' if x.get('imgFit') == 'photo' else 'cut', esc(x['img']), esc(name)))
    c = x.get('imgCredit')
    if c:
        cred = ' <a href="%s" target="_blank" rel="noopener">%s</a>%s.' % (esc(c.get('url', '')), esc(c.get('text', '')),
               (' (<a href="%s" target="_blank" rel="noopener license">license</a>)' % esc(c['licenseUrl'])) if c.get('licenseUrl') else '')
    return ('<p class="sub"><a href="/home/home-ev-chargers-batteries/">All gear</a> <span class="dot">/</span> %s</p>'
            '<div class="hwhero hgd">%s<div><p class="sub">%s</p><p>%s</p>%s</div></div>'
            '<h2>Specifications</h2><div class="scroll" tabindex="0"><table><tbody>%s</tbody></table></div>%s'
            '<p class="fh">Source: %s.%s</p>') % (
        esc(name), pic, esc(maker or ''), esc(x.get('blurb') or x.get('note') or ''),
        ('<p><a class="btn secondary" href="%s" rel="noopener">Manufacturer site</a></p>' % esc(x['website'])) if x.get('website') else '',
        table, ('<p class="fh">%s</p>' % esc(note)) if note else '', esc(x.get('source') or 'Manufacturer and public reporting, 2026'), cred)


def product_detail_html(p):
    """Static product page body (the script redraws it on load)."""
    rows = lambda lst: '<table>%s</table>' % ''.join('<tr><th>%s</th><td>%s</td></tr>' % (esc(str(a)), esc(str(b))) for a, b in (lst or []))
    adapt = ''
    if p.get('amps') and p.get('kw'):
        adapt = ('<h2>Output settings</h2><p class="sub">The output can be set below the maximum to fit the site\u2019s service. From the datasheet.</p>'
                 '<table><thead><tr><th>Output</th><th>Max draw</th>%s</tr></thead><tbody>%s</tbody></table>') % (
            '<th>Breaker</th>' if p.get('breaker') else '',
            ''.join('<tr><td>%s kW</td><td>%s A</td>%s</tr>' % (k, p['amps'].get(str(k), p['amps'].get(k, '')),
                    ('<td>%s A</td>' % p['breaker'].get(str(k), '')) if p.get('breaker') else '') for k in p['kw']))
    return ('<p class="sub"><a href="/ev-chargers/">All chargers</a> <span class="dot">/</span> %(model)s</p>'
            '<div class="hwhero"><img src="%(img)s" alt="%(model)s render" width="600" height="600"><div><p class="sub">%(oem)s</p>'
            '<p>%(blurb)s</p><p><a class="btn" href="/ev-charging-site-planner/?model=%(id)s">Use in site planner</a> '
            '<a class="btn secondary" href="%(datasheet)s" rel="noopener">Datasheet PDF</a></p></div></div>'
            '<h2>Specifications</h2><div class="hwspec">%(s1)s%(s2)s</div>%(adapt)s'
            '<h2>Certifications and standards</h2><p>%(certs)s</p>'
            '<p class="sub">Specs transcribed from the %(source)s. %(disc)s</p>') % {
        'model': esc(p['model']), 'img': esc(p.get('img', '')), 'oem': esc(p['oem']), 'blurb': esc(p.get('blurb', '')), 'id': esc(p['id']),
        'datasheet': esc(p.get('datasheet', '')), 's1': rows(p.get('spec1')), 's2': rows(p.get('spec2')), 'adapt': adapt,
        'certs': esc(p.get('certs', '')), 'source': esc(p.get('source', 'manufacturer datasheet')), 'disc': esc(p.get('disclosure', ''))}


BLOG_TITLE = 'Blog: The Charge Sheet'
BLOG_DESC = 'Notes from the business of EV charging: what is changing, what it costs, and what I would do about it. Plus a weekly screen of the news that matters.'


def post_item(p):
    kind = 'The week in charging' if p['kind'] == 'weekly' else '%d min read' % p['minutes']
    badge = (' <span class="badge-draft">%s</span>' % (('Scheduled ' + p['scheduled']) if p.get('scheduled') else 'Draft')) if p['draft'] else ''
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
            'Plus a weekly screen of the news that actually matters to people who own or plan charging sites.</p>%s</div>'
            '<div class="prose">%s<p class="feed-link"><a href="/blog/feed.xml">Subscribe with RSS</a></p></div></section>\n') % (
        BLOG_ART, '<ul class="post-list">%s</ul>' % items if items else '<p class="blog-empty">The first posts are on the way.</p>')
    h = set_meta(head, BLOG_TITLE, BLOG_DESC, url, og_default, 'home')
    ld = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'The Charge Sheet blog', 'url': url, 'description': BLOG_DESC,
          'author': dict(AUTHOR), 'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': SITE + '/blog/%s/' % p['slug'],
                                                'datePublished': p['date']} for p in posts if not p['draft']]}
    h += '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    h += '<link rel="alternate" type="application/rss+xml" title="The Charge Sheet blog" href="%s/blog/feed.xml">\n' % SITE
    live = [p for p in posts if not p['draft']]
    if not live:
        # an empty blog index is a thin page; keep it out of search until the first post is live
        h = h.replace('content="index, follow, max-image-preview:large"', 'content="noindex, follow"')
    open(os.path.join(OUT, 'blog', 'index.html'), 'w', encoding='utf-8').write(
        page_doc(h, pre_main, post_main, hollow_all, anchors, 'blog', body, 'gn-blog'))
    if live:
        urls.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, live[0]['date']))

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
                '<span class="dot">/</span><span>%s</span>%s</p><h1>%s</h1>%s%s%s</div>'
                '<article class="prose post">%s</article>'
                '<div class="prose post-foot"><div class="post-author"><img src="/img/aatish-square.jpg" alt="" width="56" height="56">'
                '<p><b>Aatish Patel</b><br>Built and ran a charging company for six years. <a href="/about/">More about me</a>.</p></div>%s'
                '<p class="feed-link"><a href="/blog/">All posts</a> <span class="dot">/</span> <a href="/blog/feed.xml">RSS</a></p></div></section>\n') % (
            p['date'], blog.nice_date(p['date']), esc(kind), (' <span class="badge-draft">%s</span>' % (('Scheduled ' + p['scheduled']) if p.get('scheduled') else 'Draft')) if p['draft'] else '',
            esc(p['title']), '<p>%s</p>' % esc(p['description']) if p['description'] else '', tags, p.get('art', ''), p['html'], more)
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
            p.get('feed_html', p['html']).replace(']]>', ']]&gt;').replace('href="/', 'href="%s/' % SITE).replace('src="/', 'src="%s/' % SITE),
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
    if not HOME_ON:
        src = re.sub(r'<!--home-side-->.*?<!--/home-side-->', '', src, flags=re.S)
        src = re.sub(r'/\*home-side\*/.*?/\*/home-side\*/', '', src, flags=re.S)
    updated = last_updated()
    page_dates = section_dates(src, updated)
    read_groups(src)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'assets'))

    # CSS and JS out to cached files
    styles = re.findall(r'<style>(.*?)</style>', src, re.S)
    scripts = re.findall(r'<script>(.*?)</script>', src, re.S)
    assert len(scripts) == 1, 'expected exactly one inline <script> in index.html'
    css = absolutize_css('\n'.join(styles))
    js = absolutize_js(scripts[0])
    # Two bundles: the home-side code (a third of the script) only ships on the /home/ pages.
    js_biz = re.sub(r'/\*home-side\*/.*?/\*/home-side\*/', '', js, flags=re.S)
    js_home = js
    css_path = hashed('site', 'css', css)
    open(os.path.join(OUT, css_path), 'w', encoding='utf-8').write(css)
    JS_PATHS['biz'] = hashed('site', 'js', minify_js(js_biz))
    JS_PATHS['home'] = hashed('site-home', 'js', minify_js(js_home)) if js_home != js_biz else JS_PATHS['biz']
    for k, code in (('biz', js_biz), ('home', js_home)):
        open(os.path.join(OUT, JS_PATHS[k]), 'w', encoding='utf-8').write(minify_js(code))
    state = {'first': True}

    def style_repl(m):
        if state['first']:
            state['first'] = False
            return '<link rel="stylesheet" href="/%s">' % css_path
        return ''
    src = re.sub(r'<style>.*?</style>', style_repl, src, flags=re.S)
    src = re.sub(r'<script>.*?</script>', lambda m: '%%CS_CONFIG%%' + '<script src="/%%JS%%"></script>', src, flags=re.S)
    src = absolutize_html(src)
    month = datetime.date.fromisoformat(updated).strftime('%B %Y')
    src = re.sub(r'Last updated [A-Z][a-z]+ \d{4}\.', 'Last updated %s.' % month, src)

    # charger catalog: data/products.json goes into the products-data script, on the pages that use it.
    # Both data scripts sit at the end of the body (before the app), not in <head>.
    try:
        products = open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8').read().strip()
        json.loads(products)
    except Exception:
        products = '[]'
    PRODUCTS_TAG[0] = '<script id="products-data" type="application/json">%s</script>\n' % products.replace('</', r'<\/')
    src = src.replace('<script id="products-data" type="application/json">[]</script>\n', '', 1)
    src = src.replace('<script id="home-gear-data" type="application/json">[]</script>', '', 1)
    if HOME_ON:
        try:
            g = json.load(open(os.path.join(ROOT, 'data', 'home-gear.json'), encoding='utf-8'))
            try:
                g['prices'] = json.load(open(os.path.join(ROOT, 'data', 'fuel-prices.json'), encoding='utf-8'))
            except Exception:
                pass
            gear = json.dumps(g, ensure_ascii=False, separators=(',', ':'))
        except Exception:
            gear = '{}'
        GEAR_TAG[0] = '<script id="home-gear-data" type="application/json">%s</script>\n' % gear.replace('</', r'<\/')
        try:
            gfull = json.loads(gear)
            for v in HOME_IDS:
                keep = GEAR_EXTRA.get(v, ())
                sub = {k: val for k, val in gfull.items() if k not in GEAR_OPTIONAL or k in keep}
                GEAR_TAGS[v] = '<script id="home-gear-data" type="application/json">%s</script>\n' % json.dumps(
                    sub, ensure_ascii=False, separators=(',', ':')).replace('</', r'<\/')
        except Exception:
            pass
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

    prerender_catalogs(full)
    posts = blog.load_posts(ROOT)
    full['home'] = full['home'].replace('<!--BLOG_LATEST-->', blog_latest_html(posts))

    sitemap = []
    for v, slug, title, desc, kind in PAGES:
        url = SITE + PATH[v]
        og_rel = 'og/%s.png' % ((slug or 'home') if v not in HOME_IDS else ('home-hub' if v == 'hhub' else slug.replace('/', '-')))
        image = SITE + '/' + og_rel if os.path.exists(os.path.join(ROOT, og_rel)) else SITE + '/og-image.png?v=2'
        page_head = set_meta(head, title, desc, url, image, kind) + jsonld(title, desc, url, image, kind, h1s.get(v), page_dates.get(v, updated), v)
        body = ''.join(full[x] if x == v else hollowed[x] for x, _, _ in bounds)
        if v in HOME_IDS and not HOME_LIVE:
            page_head = page_head.replace('content="index, follow, max-image-preview:large"', 'content="noindex"')
        pm = fill_snav(pre_main.replace('<html lang="en">', '<html lang="en" data-side="home">') if v in HOME_IDS else pre_main, v)
        ph = page_head.replace('<html lang="en">', '<html lang="en" data-side="home">') if v in HOME_IDS else page_head
        data_tags = (PRODUCTS_TAG[0] if v in PRODUCT_VIEWS else '') + (GEAR_TAGS.get(v, GEAR_TAG[0]) if v in HOME_IDS else '')
        doc = rewrite_links(ph + pm + body + post_main, v, anchors).replace('%%CS_CONFIG%%', data_tags + config_script(v, anchors))
        dest = os.path.join(OUT, slug, 'index.html') if slug else os.path.join(OUT, 'index.html')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'w', encoding='utf-8').write(doc)
        if v not in HOME_IDS or HOME_LIVE:
            sitemap.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, page_dates.get(v, updated)))

    # one page per charger: /ev-chargers/<id>/
    if 'hardware' in VIEWS:
        products = load_products()
        try:
            pdate = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', 'data/products.json'], cwd=ROOT,
                                   capture_output=True, text=True, timeout=10).stdout.strip() or updated
        except Exception:
            pdate = updated
        pdate = max(pdate, page_dates.get('hardware', updated))
        for p in products:
            url = SITE + '/ev-chargers/%s/' % p['id']
            title, desc = product_title(p), product_desc(p)
            name = '%s %s' % (p['oem'], p['model'])
            page_head = set_meta(head, title, desc, url, SITE + '/og-image.png?v=2', 'tool')
            ld = {'@context': 'https://schema.org', '@graph': [
                {'@type': 'WebPage', 'name': name, 'headline': title, 'description': desc, 'url': url, 'dateModified': pdate,
                 'image': SITE + p['img'] if p.get('img', '').startswith('/') else p.get('img', ''), 'inLanguage': 'en-US',
                 'author': dict(AUTHOR), 'isPartOf': {'@type': 'WebSite', 'name': SITE_NAME, 'url': SITE + '/'}},
                {'@type': 'BreadcrumbList', 'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': SITE_NAME, 'item': SITE + '/'},
                    {'@type': 'ListItem', 'position': 2, 'name': 'Chargers', 'item': SITE + '/ev-chargers/'},
                    {'@type': 'ListItem', 'position': 3, 'name': name, 'item': url}]}]}
            page_head += '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
            sec = full['hardware']
            sec = re.sub(r'<h1>.*?</h1>', '<h1>%s</h1>' % esc(name), sec, count=1, flags=re.S)
            sec = re.sub(r'(<div class="tool-head">\s*<h1>.*?</h1>\s*)<p>.*?</p>', lambda m: m.group(1) + '<p>%s</p>' % esc(desc), sec, count=1, flags=re.S)
            sec = re.sub(r'<div class="hw" id="hw-body">.*?</div>\s*</section>', lambda m: '<div class="hw" id="hw-body">%s</div>\n</section>' % product_detail_html(p), sec, count=1, flags=re.S)
            body = ''.join(sec if x == 'hardware' else hollowed[x] for x, _, _ in bounds)
            doc = rewrite_links(page_head + fill_snav(pre_main, 'hardware') + body + post_main, 'hardware', anchors).replace(
                '%%CS_CONFIG%%', PRODUCTS_TAG[0] + config_script('hardware', anchors, p['id']))
            dest = os.path.join(OUT, 'ev-chargers', p['id'], 'index.html')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'w', encoding='utf-8').write(doc)
            sitemap.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, pdate))
            PRODUCT_PAGES.append((url, name, desc))

    # one page per piece of home gear: /home/home-ev-chargers-batteries/<id>/
    if 'hgear' in VIEWS and GEAR_TAG[0]:
        try:
            gear = json.load(open(os.path.join(ROOT, 'data', 'home-gear.json'), encoding='utf-8'))
        except Exception:
            gear = {}
        try:
            gdate = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', 'data/home-gear.json'], cwd=ROOT,
                                   capture_output=True, text=True, timeout=10).stdout.strip() or updated
        except Exception:
            gdate = updated
        gdate = max(gdate, page_dates.get('hgear', updated), HOME_PUBLISHED)
        base = PATH['hgear']
        for kind, x in gear_items(gear):
            name, title, desc = gear_meta(kind, x)
            url = SITE + base + x['id'] + '/'
            page_head = set_meta(head, title, desc, url, SITE + '/og/home-home-ev-chargers-batteries.png', 'tool')
            ld = {'@context': 'https://schema.org', '@graph': [
                {'@type': 'WebPage', 'name': name, 'headline': title, 'description': desc, 'url': url, 'dateModified': gdate,
                 **({'primaryImageOfPage': {'@type': 'ImageObject', 'url': SITE + '/' + x['img']}} if x.get('img') else {}),
                 'inLanguage': 'en-US', 'author': dict(AUTHOR), 'isPartOf': {'@type': 'WebSite', 'name': SITE_NAME, 'url': SITE + '/'}},
                {'@type': 'BreadcrumbList', 'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': SITE_NAME, 'item': SITE + '/'},
                    {'@type': 'ListItem', 'position': 2, 'name': 'At home', 'item': SITE + '/home/'},
                    {'@type': 'ListItem', 'position': 3, 'name': 'Home gear', 'item': SITE + base},
                    {'@type': 'ListItem', 'position': 4, 'name': name, 'item': url}]}]}
            page_head += '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
            sec = full['hgear']
            sec = re.sub(r'<h1>.*?</h1>', '<h1>%s</h1>' % esc(name), sec, count=1, flags=re.S)
            sec = re.sub(r'(<div class="tool-head">\s*<h1>.*?</h1>\s*)<p>.*?</p>', lambda m: m.group(1) + '<p>%s</p>' % esc(desc), sec, count=1, flags=re.S)
            sec = re.sub(r'<div class="wrap hgear" id="h-gear">.*?</div>\s*</section>',
                         lambda m: '<div class="wrap hgear" id="h-gear">%s</div>\n</section>' % gear_detail_html(kind, x, name), sec, count=1, flags=re.S)
            body = ''.join(sec if v2 == 'hgear' else hollowed[v2] for v2, _, _ in bounds)
            ph = page_head.replace('<html lang="en">', '<html lang="en" data-side="home">')
            pm = fill_snav(pre_main.replace('<html lang="en">', '<html lang="en" data-side="home">'), 'hgear')
            doc = rewrite_links(ph + pm + body + post_main, 'hgear', anchors).replace(
                '%%CS_CONFIG%%', GEAR_TAGS.get('hgear', GEAR_TAG[0]) + config_script('hgear', anchors, x['id']))
            dest = os.path.join(OUT, base.strip('/'), x['id'], 'index.html')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'w', encoding='utf-8').write(doc)
            if HOME_LIVE:
                sitemap.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url, gdate))
                GEAR_PAGES.append((url, name, desc))

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
    write_llms_txt(h1s)
    point_scripts()
    headers = open(os.path.join(ROOT, '_headers')).read().rstrip()
    headers += '\n\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n\n/og/*\n  Cache-Control: public, max-age=604800\n'
    open(os.path.join(OUT, '_headers'), 'w').write(headers)
    redirects = ['/index.html / 301']
    for v, slug, *_ in PAGES:
        if slug and v != slug:
            redirects += ['/%s %s 301' % (v, PATH[v]), '/%s/ %s 301' % (v, PATH[v])]
    open(os.path.join(OUT, '_redirects'), 'w').write('\n'.join(redirects) + '\n')

    # static files
    for d in ('fonts', 'img', 'data', 'og', 'datasheets'):
        if os.path.isdir(os.path.join(ROOT, d)):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT, d))
    for f in ('favicon.svg', 'favicon-32.png', 'apple-touch-icon.png', 'og-image.png'):
        shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))

    sizes = sorted(os.path.getsize(os.path.join(OUT, p[1], 'index.html') if p[1] else os.path.join(OUT, 'index.html')) for p in PAGES)
    jsk = lambda k: os.path.getsize(os.path.join(OUT, JS_PATHS[k])) // 1024
    print('Built %d pages into dist/ (updated %s). Page HTML %d to %d KB; CSS %d KB, JS %d KB (home pages %d KB).' % (
        len(PAGES), updated, sizes[0] // 1024, sizes[-1] // 1024, len(css) // 1024, jsk('biz'), jsk('home')))


if __name__ == '__main__':
    build()

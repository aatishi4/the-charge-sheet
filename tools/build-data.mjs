#!/usr/bin/env node
/**
 * build-data.mjs
 *
 * Downloads open EV charging and traffic data and writes compact JSON files
 * that The Charge Sheet reads locally, with no API calls at runtime.
 *
 * Requires Node 18 or newer. No dependencies.
 *
 * Examples:
 *   node tools/build-data.mjs --stations --state IL --nrel-key YOURKEY
 *   node tools/build-data.mjs --stations --state IL --ocm-key YOURKEY --source ocm
 *   node tools/build-data.mjs --aadt --state IL
 *   node tools/build-data.mjs --aadt --layer https://example.gov/arcgis/rest/services/AADT/FeatureServer/0 --state TX
 *
 * Output lands in ./data and is listed in ./data/manifest.json, which the page
 * loads automatically when you serve the site yourself.
 *
 * Licensing, briefly:
 *   AFDC data comes from the US Department of Energy and is free to use.
 *   Open Charge Map data is CC BY-SA 4.0, so credit them and share alike.
 *   State DOT traffic layers are public records. Credit the agency.
 *   PlugShare is neither of these. Its API is licensed commercially and its
 *   terms do not allow scraping, so it is deliberately not supported here.
 */

import fs from 'node:fs/promises';
import path from 'node:path';

const args = process.argv.slice(2);
const flag = (name) => args.includes('--' + name);
const opt = (name, fallback = null) => {
  const i = args.indexOf('--' + name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const OUT = opt('out', './data');
const STATE = (opt('state') || '').toUpperCase();
const RADIUS_ROUND = 5; // decimal places kept on coordinates

/* Traffic layers that are known to work. Add your own with --layer. */
const LAYERS = {
  CA: 'https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHhighway/Traffic_AADT/FeatureServer/0',
  WA: 'https://data.wsdot.wa.gov/arcgis/rest/services/Shared/TrafficData/FeatureServer/0',
  IL: 'https://services2.arcgis.com/aIrBD8yn1TDTEXoz/ArcGIS/rest/services/ADT_COMP_2020Dissolved/FeatureServer/0',
  WI: 'https://services5.arcgis.com/0pgGLzT0Nh7FVjon/ArcGIS/rest/services/TCMap_Traffic_Count_Sites/FeatureServer/0',
  KS: 'https://kanplan.ksdot.gov/arcgis_web_adaptor/rest/services/Transportation/AADT_Flow_Map/FeatureServer/0',
  CT: 'https://services1.arcgis.com/FCaUeJ5SOVtImake/arcgis/rest/services/AADT/FeatureServer/0'
};

const round = (n) => Math.round(n * 10 ** RADIUS_ROUND) / 10 ** RADIUS_ROUND;
const today = () => new Date().toISOString().slice(0, 10);

async function getJSON(url) {
  const res = await fetch(url, { headers: { 'User-Agent': 'the-charge-sheet/1.0' } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url.split('?')[0]}`);
  return res.json();
}

/* ---------- Charging stations ---------- */

async function buildStationsAFDC(key) {
  if (!key) throw new Error('Need --nrel-key. Free at developer.nlr.gov/signup');
  const url = 'https://developer.nlr.gov/api/alt-fuel-stations/v1.json'
    + `?api_key=${encodeURIComponent(key)}&fuel_type=ELEC&status=E&access=public&limit=all`
    + (STATE ? `&state=${STATE}` : '');
  console.log(`Fetching AFDC stations${STATE ? ' for ' + STATE : ' nationwide'}...`);
  const data = await getJSON(url);
  const rows = (data.fuel_stations || [])
    .filter((s) => s.latitude && s.longitude)
    .map((s) => [round(s.latitude), round(s.longitude), Number(s.ev_dc_fast_num || 0), Number(s.ev_level2_evse_num || 0)])
    .filter((r) => r[2] > 0 || r[3] > 0);
  return { type: 'stations', source: 'AFDC (US DOE)', state: STATE || 'US', updated: today(), rows };
}

async function buildStationsOCM(key) {
  if (!key) throw new Error('Need --ocm-key. Free at openchargemap.org/site/develop');
  const url = 'https://api.openchargemap.io/v3/poi'
    + `?key=${encodeURIComponent(key)}&countrycode=US&maxresults=100000&compact=true&verbose=false`
    + (STATE ? `&stateorprovince=${STATE}` : '');
  console.log('Fetching Open Charge Map points...');
  const data = await getJSON(url);
  const rows = (data || [])
    .filter((p) => p.AddressInfo && p.AddressInfo.Latitude)
    .map((p) => {
      let dc = 0, l2 = 0;
      (p.Connections || []).forEach((c) => {
        const qty = Number(c.Quantity || 1);
        const kw = Number(c.PowerKW || 0);
        if (kw >= 25) dc += qty; else if (kw >= 3) l2 += qty;
      });
      return [round(p.AddressInfo.Latitude), round(p.AddressInfo.Longitude), dc, l2];
    })
    .filter((r) => r[2] > 0 || r[3] > 0);
  return { type: 'stations', source: 'Open Charge Map (CC BY-SA 4.0)', state: STATE || 'US', updated: today(), rows };
}

/* ---------- Traffic counts ---------- */

function pickVolumeField(fields) {
  const good = /aadt|adt|volume/i;
  const bad = /year|yr|date|type|pct|percent|truck|hcv|^mu_|^su_|class|_id$|^id$|flag|comb/i;
  const hit = fields.find((f) => good.test(f.name) && !bad.test(f.name) && /Integer|Double|Single|Small/i.test(f.type));
  return hit ? hit.name : null;
}

async function buildAADT(layer) {
  const url = layer || LAYERS[STATE];
  if (!url) throw new Error(`No known layer for ${STATE || 'that state'}. Pass one with --layer.`);
  const meta = await getJSON(url.replace(/\/$/, '') + '?f=json');
  const field = opt('field') || pickVolumeField(meta.fields || []);
  if (!field) throw new Error('Could not find a traffic volume field. Pass one with --field.');
  console.log(`Using field "${field}" from ${meta.name || 'layer'}. Paging...`);

  const rows = [];
  const pageSize = Math.min(Number(meta.maxRecordCount || 1000), 2000);
  let offset = 0;
  for (;;) {
    const q = url.replace(/\/$/, '') + '/query?f=json&where=' + encodeURIComponent(`${field} > 0`)
      + `&outFields=${encodeURIComponent(field)}&returnGeometry=true&outSR=4326`
      + `&resultOffset=${offset}&resultRecordCount=${pageSize}`;
    const page = await getJSON(q);
    if (page.error) throw new Error(page.error.message || 'layer query failed');
    const feats = page.features || [];
    for (const f of feats) {
      const g = f.geometry;
      const v = Number(f.attributes[field]);
      if (!g || !isFinite(v) || v <= 0) continue;
      // Points come back as x/y. Lines come back as paths: take the midpoint.
      let lon, lat;
      if (typeof g.x === 'number') { lon = g.x; lat = g.y; }
      else if (g.paths && g.paths[0] && g.paths[0].length) {
        const pts = g.paths[0];
        const mid = pts[Math.floor(pts.length / 2)];
        lon = mid[0]; lat = mid[1];
      } else continue;
      rows.push([round(lat), round(lon), Math.round(v)]);
    }
    process.stdout.write(`\r  ${rows.length} points`);
    if (feats.length < pageSize || !page.exceededTransferLimit && feats.length === 0) break;
    if (feats.length === 0) break;
    offset += feats.length;
    if (offset > 400000) break; // sanity stop
  }
  console.log('');
  return { type: 'aadt', source: meta.name || url, state: STATE || 'unknown', field, updated: today(), rows };
}

/* ---------- Write ---------- */

async function writeOut(name, payload) {
  await fs.mkdir(OUT, { recursive: true });
  const file = path.join(OUT, name);
  await fs.writeFile(file, JSON.stringify(payload));
  const kb = Math.round((await fs.stat(file)).size / 1024);
  console.log(`Wrote ${file}: ${payload.rows.length} rows, ${kb} KB`);

  let files = [];
  const manifestPath = path.join(OUT, 'manifest.json');
  try { files = JSON.parse(await fs.readFile(manifestPath, 'utf8')).files || []; } catch {}
  if (!files.includes(name)) files.push(name);
  await fs.writeFile(manifestPath, JSON.stringify({ files, updated: today() }, null, 2));
}

async function main() {
  if (!flag('stations') && !flag('aadt')) {
    console.log('Nothing to do. Pass --stations, --aadt, or both. See the comments at the top of this file.');
    return;
  }
  if (flag('stations')) {
    const source = opt('source', 'afdc');
    const data = source === 'ocm'
      ? await buildStationsOCM(opt('ocm-key') || process.env.OCM_API_KEY)
      : await buildStationsAFDC(opt('nrel-key') || process.env.NREL_API_KEY);
    await writeOut(STATE ? `stations-${STATE.toLowerCase()}.json` : 'stations.json', data);
  }
  if (flag('aadt')) {
    const data = await buildAADT(opt('layer'));
    await writeOut(`aadt-${(STATE || 'custom').toLowerCase()}.json`, data);
  }
  console.log('Done. Serve the site and the page will load these automatically, or load them by hand in the forecast.');
}

main().catch((e) => { console.error('Failed:', e.message); process.exit(1); });

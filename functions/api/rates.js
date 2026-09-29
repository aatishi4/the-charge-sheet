// Cloudflare Pages Function: GET /api/rates?zip=60477
// Looks up current residential electric rates for a ZIP code in the OpenEI Utility Rate Database,
// keeps only what the home charging calculator needs, and caches the answer at the edge for a day.
// Needs one secret in Cloudflare Pages settings: OPENEI_KEY (free at https://openei.org/services/api/signup/).
// Without it, the endpoint answers {error:"not_configured"} and the calculator falls back to presets.

const TTL = 86400;

function json(body, status, extra) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: Object.assign({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=' + TTL }, extra || {}),
  });
}

function trim(r) {
  const tiers = (r.energyratestructure || []).map((per) => (per || []).slice(0, 3).map((t) => ({ rate: Number(t.rate || 0), adj: Number(t.adj || 0), max: t.max || null })));
  return {
    label: r.label, name: r.name, utility: r.utility, eiaid: r.eiaid, startdate: r.startdate || null, enddate: r.enddate || null,
    fixedchargefirstmeter: r.fixedchargefirstmeter || 0, fixedchargeunits: r.fixedchargeunits || '$/month',
    energyratestructure: tiers, energyweekdayschedule: r.energyweekdayschedule || [], energyweekendschedule: r.energyweekendschedule || [],
    uri: r.uri || '',
  };
}

export async function onRequestGet({ request, env, waitUntil }) {
  const url = new URL(request.url);
  const zip = (url.searchParams.get('zip') || '').trim();
  if (!/^\d{5}$/.test(zip)) return json({ error: 'bad_zip' }, 400, { 'cache-control': 'no-store' });
  if (!env.OPENEI_KEY) return json({ error: 'not_configured' }, 503, { 'cache-control': 'no-store' });

  const cache = caches.default;
  const cacheKey = new Request(url.origin + '/api/rates?zip=' + zip, { method: 'GET' });
  const hit = await cache.match(cacheKey);
  if (hit) return hit;

  const q = new URLSearchParams({
    version: '8', format: 'json', api_key: env.OPENEI_KEY, address: zip, sector: 'Residential',
    approved: 'true', detail: 'full', limit: '100', orderby: 'startdate', direction: 'desc',
  });
  let data;
  try {
    const res = await fetch('https://api.openei.org/utility_rates?' + q.toString(), { cf: { cacheTtl: TTL } });
    if (!res.ok) return json({ error: 'upstream_' + res.status }, 502, { 'cache-control': 'no-store' });
    data = await res.json();
  } catch (e) {
    return json({ error: 'upstream_unreachable' }, 502, { 'cache-control': 'no-store' });
  }
  if (data && data.error) return json({ error: 'upstream_error' }, 502, { 'cache-control': 'no-store' });

  const now = Date.now() / 1000;
  const seen = new Set();
  const items = (data.items || [])
    .filter((r) => !r.enddate || r.enddate > now)
    .filter((r) => r.energyratestructure && r.energyratestructure.length)
    .filter((r) => { const k = (r.utility || '') + '|' + (r.name || ''); if (seen.has(k)) return false; seen.add(k); return true; }) // newest version of each plan
    .slice(0, 40)
    .map(trim);

  const out = json({ zip, count: items.length, items, source: 'OpenEI Utility Rate Database' });
  waitUntil(cache.put(cacheKey, out.clone()));
  return out;
}

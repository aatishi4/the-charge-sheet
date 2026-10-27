// The Charge Sheet scheduler: publishes scheduled blog posts on time.
//
// Every 5 minutes (Cloudflare's clock, which actually runs on time, unlike GitHub's)
// it reads chargesheet.io/blog/schedule.json. Each site build writes that file with the
// publish times of posts that weren't live yet when the build ran. If one of those times
// has passed, the live site is stale, so the Worker calls the Pages deploy hook and
// Cloudflare rebuilds. Once the rebuild lands, that time drops out of schedule.json and
// the Worker goes back to doing nothing. No state to keep.
//
// Setup: see "Scheduled posts" in DEPLOY.md. Needs one secret, DEPLOY_HOOK.
// GET on the Worker's URL shows what it would do right now without triggering anything.

const SITE = 'https://chargesheet.io';

// Only chase a due post for 30 minutes. If the build itself is broken, this stops it
// from burning the Pages build quota (500 a month on the free plan): six tries, max.
// After that, the GitHub workflow is the backstop, and you'll want to look anyway.
const WINDOW_MS = 30 * 60 * 1000;

export async function check(now, fetchFn = fetch) {
  const res = await fetchFn(`${SITE}/blog/schedule.json?t=${now}`, {
    headers: { 'User-Agent': 'charge-sheet-scheduler', 'Cache-Control': 'no-cache' },
    cf: { cacheTtl: 0 },
  });
  if (!res.ok) return { rebuild: false, reason: `schedule.json returned ${res.status}` };
  const s = await res.json();
  const due = (s.upcoming || []).filter((t) => {
    const at = Date.parse(t);
    return at <= now && now - at < WINDOW_MS;
  });
  const built = Date.parse(s.built);
  if (!due.length) return { rebuild: false, reason: 'nothing due', built: s.built, upcoming: s.upcoming };
  // A build that ran after the due time already published it, even if schedule.json looks stale.
  if (built >= Math.max(...due.map(Date.parse))) return { rebuild: false, reason: 'already built after due time', built: s.built };
  return { rebuild: true, due, built: s.built };
}

async function trigger(env) {
  if (!env.DEPLOY_HOOK) throw new Error('DEPLOY_HOOK secret is not set');
  const res = await fetch(env.DEPLOY_HOOK, { method: 'POST' });
  if (!res.ok) throw new Error(`deploy hook returned ${res.status}`);
}

export default {
  async scheduled(event, env, ctx) {
    const now = Date.now();
    const r = await check(now);
    if (!r.rebuild) return;
    console.log(`due ${r.due.join(', ')}; live build from ${r.built}; rebuilding`);
    await trigger(env);
  },

  async fetch(request) {
    const r = await check(Date.now());
    return new Response(JSON.stringify(r, null, 2) + '\n', {
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    });
  },
};

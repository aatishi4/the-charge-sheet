// Cloudflare Pages Function: /api/report-email
//   GET  -> {ready: true|false}. The report page only shows "Email me this report" when this says ready.
//   POST -> emails the visitor a plain-text copy of their project report through Resend, then forwards
//           the lead (email, site name, source, opt-in) to the Formspree form so it lands in Aatish's inbox.
//
// Needs two secrets in Cloudflare Pages (Settings > Variables and Secrets): RESEND_API_KEY and REPORT_FROM,
// for example  The Charge Sheet <reports@chargesheet.io>  (the domain must be verified in Resend).
// Optional: REPORT_REPLY_TO (replies go here) and FORMSPREE_URL (defaults to the site's contact form).
// Without RESEND_API_KEY the function answers ready:false and the form never appears.

const FORMSPREE_DEFAULT = 'https://formspree.io/f/moevldnd';
const MAX_REPORT = 20500;

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}

function originOk(request) {
  const o = request.headers.get('origin');
  if (!o) return false; // browsers always send Origin on a POST from the page
  try {
    const h = new URL(o).hostname;
    return h === 'chargesheet.io' || h.endsWith('.chargesheet.io') || h === 'the-charge-sheet.pages.dev' || h.endsWith('.the-charge-sheet.pages.dev') || h === 'localhost';
  } catch (e) { return false; }
}

export async function onRequestGet({ env }) {
  return json({ ready: !!(env.RESEND_API_KEY && env.REPORT_FROM) });
}

export async function onRequestPost({ request, env, waitUntil }) {
  if (!originOk(request)) return json({ error: 'origin' }, 403);
  if (!env.RESEND_API_KEY || !env.REPORT_FROM) return json({ error: 'not_configured' }, 503);

  let b;
  try { b = await request.json(); } catch (e) { return json({ error: 'bad_json' }, 400); }
  const email = String(b.email || '').trim();
  const report = String(b.report || '');
  if (b.website) return json({ ok: true }); // honeypot: pretend it worked
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || email.length > 200) return json({ error: 'bad_email' }, 400);
  // The text must look like a report the site made. No links, so this can't be used to mail ads.
  if (!report.startsWith('PROJECT REPORT') || report.indexOf('== ') < 0 || report.length > MAX_REPORT || /https?:\/\/|www\./i.test(report)) {
    return json({ error: 'bad_report' }, 400);
  }

  const site = String(b.name || '').trim().slice(0, 80);
  const text = [
    'Here is the project report you saved on The Charge Sheet' + (site ? ' for ' + site : '') + '.',
    'The numbers are ballpark estimates from free tools. Check them against a real quote before you sign anything.',
    '',
    report,
    '',
    'To save it as a PDF, open chargesheet.io, go to your project report and use Export PDF.',
    'Questions about the project? Reply to this email.',
    '',
    'Aatish Patel',
    'chargesheet.io',
  ].join('\n');

  const mail = { from: env.REPORT_FROM, to: [email], subject: 'Your Charge Sheet project report', text };
  if (env.REPORT_REPLY_TO) mail.reply_to = env.REPORT_REPLY_TO;
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify(mail),
  });
  if (!res.ok) return json({ error: 'send_failed' }, 502);

  const s = b.source && typeof b.source === 'object' ? b.source : {};
  const u = s.utm && typeof s.utm === 'object' ? s.utm : {};
  const lead = {
    _subject: 'Charge Sheet report emailed' + (site ? ': ' + site : ''),
    email,
    site,
    optin: b.optin ? 'yes' : 'no',
    source: String(s.label || '').slice(0, 120),
    utm_source: u.utm_source || '', utm_medium: u.utm_medium || '', utm_campaign: u.utm_campaign || '', utm_content: u.utm_content || '',
    landing: String(s.landing || '').slice(0, 200), referrer: String(s.ref || '').slice(0, 120),
    page: String(b.page || '').slice(0, 200),
    message: 'Emailed a project report (' + report.split('\n').filter((l) => l.startsWith('== ')).length + ' tools).',
  };
  const p = fetch(env.FORMSPREE_URL || FORMSPREE_DEFAULT, {
    method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify(lead),
  }).catch(() => {});
  if (typeof waitUntil === 'function') waitUntil(p);
  return json({ ok: true });
}

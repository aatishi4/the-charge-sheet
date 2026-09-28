# The Charge Sheet blog: playbook

Last updated 2026-09-28. The working manual for the blog: the Monday run reads it, and any session drafting or scheduling a post follows it. Aatish keeps a private idea backlog outside the repo; end each Monday run with a "For the backlog" list (new ideas he raised, in his words, and questions he skipped).

## The weekly rhythm

1. Monday morning (about 7am CT) a scheduled run scans the past 7 days of news, picks 3 stories, and asks Aatish 4 to 6 questions.
2. Aatish answers in that run whenever he gets to it. Messy, voice-transcribed, one-word answers are all fine. "Skip" is a valid answer.
3. The run drafts the weekly post (and an essay if an answer earned one), pushes to a `post/<slug>` branch, and sends the preview link.
4. Nothing goes live until Aatish says merge. Merged posts go out on the next open Tuesday or Thursday at 9am Central.

## Voice

- First person, Aatish: an operator who built and ran a charging business for six years. Knows the hardware, the sales cycle, the utility bill and the pro forma.
- Dry, blunt, self-aware, a one-liner where it earns its place. Not a hype account, not a doom account.
- No em dashes. Bullets end with periods. Short paragraphs.
- Never a sales pitch. No vendor recommendations he hasn't made himself.
- Never invent his opinion. His take comes from his answers. If a story got no answer, it gets facts only, or it gets cut.
- Don't publish default-based calculator results (break-even sessions, fleet 80 vs 100%) in copy. Link to the calculator instead.
- Don't name or hint at XCharge customers, partners, or anything non-public from his time there. Benchmark sites stay anonymized as they are on the Benchmarks page. When he names one of his own sites in an answer, write "one of my sites".

## Weekly post format (kind: weekly)

- File: `posts/YYYY-MM-DD-<slug>.md`, dated the Monday of the run while it's a draft, then renamed to its publish day when scheduled (see Publishing schedule). Front matter: title, description (1 to 2 sentences, under 160 chars), date, tags, `kind: weekly`, `draft: true`.
- Title: the sharpest claim of the week, not "Weekly roundup #12".
- Opening line: "Three things worth your time this week, and one thing I would do about them." (Vary it once it gets stale.)
- Three numbered sections. Each: a claim-style H2, 1 to 2 short paragraphs of facts with bold numbers and inline source links, then **Why it matters:** in his voice from his answer.
- Then **What I'd do** (one action for a site host, operator or fleet manager).
- Optional **History rhymes** section (3 to 5 sentences) when he answered the history question.
- Close with links into the site where relevant (guide or tool URLs below).
- 600 to 900 words. Readers are busy.

## Essay format (kind: essay)

- Comes from an answer with more in it than a weekly post can hold. 800 to 1,500 words.
- Same voice rules. One argument per essay. A concrete story or number in the first three paragraphs.
- If the answer isn't enough for a full essay, put it in the "For the backlog" list with his words and the follow-up question it needs.

## The questions (4 to 6 per week)

- 2 or 3 story questions, one per picked story: ask for his take, not a summary. Good: "Walmart is at $0.43 and owns the parking lot. If you were a c-store owner with two DCFCs down the road, do you match, ignore, or change what you sell?" Bad: "What do you think about Walmart's pricing?"
- 1 history question: pair one story with a historical parallel and ask whether it holds or breaks. Include the one-line history so he doesn't have to look it up. Keep it plain: state the parallel in one sentence, then ask one simple either/or. (2026-09-28: the railroad gauge question read as too abstract and he skipped it.)
- 1 or 2 evergreen prompts from the Essay prompt bank (or a backlog follow-up if Aatish pasted any into the run). Rotate; don't repeat within 8 weeks.
- Each question answerable out loud in about 2 minutes. Number them. Put the 3 stories (headline, 2-line summary, source link) above the questions so he has context.

## News scan

Window: the past 7 days. Scope, in priority order:
1. EVSE business and policy: networks, pricing, utilization, reliability, NEVI and other federal or state funding, utility tariffs, demand charges, make-ready programs, NACS/J3400 transition at the site level.
2. Fleet electrification: depot charging, medium and heavy duty, fleet TCO, school and transit buses.
3. EV market: sales and share, OEM strategy shifts, used EV prices, model launches that change charging demand.
4. History rhymes: any story where electrification repeats an older build-out.

Storage and grid only when it directly touches charging sites.

Where to look (start here, go wider as needed): Electrek, InsideEVs, Utility Dive, Canary Media, Charged EVs, Reuters autos and energy, Bloomberg Green headlines, Tom Moloughney's State of Charge trackers, Paren reliability and pricing reports, Stable Auto, Cox Automotive / Kelley Blue Book EV sales reports, Argonne light-duty sales data, AFDC station counts, FHWA NEVI updates, state energy office and PUC dockets, FreightWaves, Trucking Dive, ACT News, CALSTART.

Rules:
- Pick stories that change a decision for a site host, operator or fleet, not the loudest headline.
- Every number gets an inline link to where it came from. Prefer the primary source (report, filing, press release, docket) over the article about it.
- Cross-check any number that carries the argument against a second source. If they disagree, say so or drop it.
- No quote longer than 15 words. Paraphrase.
- Don't repeat a story covered in the Topic log unless there is new data.

## Site links to use

Guides: /how-ev-charging-works/, /ev-charging-business-model/, /ev-charging-site-selection/, /ev-charging-station-financing/, /battery-storage-ev-charging/, /ev-charger-connectivity/, /buying-ev-chargers/, /fleet-ev-charging/, /ev-charging-benchmarks/, /ev-charging-glossary/.
Tools: /ev-charging-site-planner/, /ev-charger-installation-cost/, /sba-loan-calculator-ev-charging/, /fleet-charging-calculator/, /ev-charging-utilization-forecast/, /ev-charger-cellular-signal-check/.

## Art, figures and photos

Every post gets line art in the site's style. Photos are optional.

- **Header art (every post):** `posts/art/<slug>.svg`, `viewBox="0 0 720 150"`. Or set `art: <spot>` in front matter to reuse a site spot (basics, primer, realestate, finance, storage, connectivity, vendors, fleet, benchmarks). With neither, the post falls back to the generic blog spot.
- **Figures (one per post that has a number worth seeing):** a line of its own, `{{art <name> | Caption in Markdown.}}`, drawing from `posts/art/<name>.svg`, 720 wide, any height. Plays when scrolled into view. The caption is the figure's accessible label, so it must say what the figure shows, including the key numbers and the source. Conceptual figures say "Illustrative, not a forecast." No default-based calculator numbers.
- **Drawing vocabulary** (from tools/spots.py): strokes `ln` (ink), `lt` (light line), `lb` (blue), `la` (amber), `dash`; fills `fm fw fi fb fa fas fs`; text classes `b` and `a`. Animations: `d` (draws a stroke; needs `pathLength="1"`, and it overrides `dash`), `fade`, `grow` (bars up), `growx` (bars across), `flow` (moving dashes), `ping`, `bob`. Stagger with `style="--d:.3s"`; keep a figure's whole sequence under about 3 seconds.
- **Legibility:** header labels are 11px and hidden on phones, so header art must read without words. Figure text is 14px in a 720-wide drawing, which renders around 7px on a phone. Keep figure labels short and let the caption carry the numbers.
- **Check before pushing:** `SHOW_DRAFTS=1 python3 tools/build_pages.py`, then screenshot the post in light and dark, desktop and phone. Reduced-motion and no-JavaScript both show the finished drawing.
- **Photos:** `{{photo <src> | alt text | credit in Markdown}}`. Store downloads in `img/blog/`, at most 1600px wide, JPEG around 80% quality.
  - First choice for history pieces: public-domain archives (Library of Congress, National Archives, Wikimedia Commons items marked public domain). Credit the archive.
  - Stock: Unsplash, through the Unsplash connector if it's connected. Use the image URL the API returns (Unsplash requires hotlinking) and credit "Photo: <name> on Unsplash" with both linked.
  - Never: news photos or anything scraped, AI images of real people, brands or places, or photos that identify XCharge sites or customers.

## Publishing

- Repo: github.com/aatishi4/the-charge-sheet. Branch `post/<slug>`; preview at `https://post-<slug>.the-charge-sheet.pages.dev/blog/<slug>/` (drafts show on previews, 404 on chargesheet.io).
- Build check before pushing: `SHOW_DRAFTS=1 python3 tools/build_pages.py` must run clean and the post must render.
- On "merge": schedule it (see Publishing schedule) and merge to main.
- If the push is refused (the scheduled session may not be authorized for the repo): save the post and a `git format-patch` somewhere Aatish can reach (the Project's `claude/blog-queue/`) and send them as files. Say plainly that it wasn't pushed.

## Publishing schedule

- Posts go live **Tuesdays and Thursdays at 9:00am Central**. Scheduled posts carry `publish: YYYY-MM-DDT09:00:00-05:00` in front matter (use `-05:00` during daylight time, `-06:00` from the first Sunday in November to the second Sunday in March), and `date:` and the file name match that day. Scheduled posts have no `draft: true`.
- Until its publish time a post shows only on preview builds, with a "Scheduled <date>" badge. It is left out of the live blog, feed, sitemap and home page.
- The Scheduled publish workflow (`.github/workflows/scheduled-publish.yml`) runs Tuesdays and Thursdays at 14:00 and 15:00 UTC (9am Central in daylight and standard time). If a due post isn't in the live feed, it triggers a rebuild: the Cloudflare deploy hook in the `CF_DEPLOY_HOOK` secret if set, otherwise an empty commit on main. `tools/due_posts.py` does the check; `BLOG_NOW=2026-10-06T14:05:00Z python3 tools/build_pages.py` shows what the live site will look like at a given time.
- On "merge": remove `draft: true`, give the post the next open slot (rules below), rename the file to that date, set `date:` and `publish:`, and merge to main. The post goes live at 9am on its day, not at merge. Tell Aatish the date it landed on.
- Slot rule: a weekly takes the earliest Tuesday that doesn't already hold a weekly, and any essay it displaces moves to the next open slot. Essays take the next open slot in order.
- A weekly that goes out more than a few days after its news opens with "Three things from <period> worth your time..." instead of "this week", and cross-links earlier posts it builds on.
- On a post's publish day, confirm `https://chargesheet.io/blog/<slug>/` returns 200 and the post is in `/blog/feed.xml`.

## History bank (leads to verify before using; add as you go)

- Before drive-in gas stations (first purpose-built ones around 1913), drivers bought gasoline at general stores, pharmacies and hardware stores. Curbside pumps at existing businesses: destination charging.
- AC vs DC, Edison vs Westinghouse (1880s to 1890s): a standards war won by the option that scaled cheaper. Parallel: CCS vs NACS vs CHAdeMO.
- Rural Electrification Administration (1936): private utilities wouldn't serve farms because density didn't pencil. Parallel: rural corridors, NEVI, "only charger for miles".
- Around 1900, electric cars were a large share of US cars; Detroit Electric and Baker sold to city buyers. Range, roads and the electric starter (1912) killed them.
- Hartford Electric Light Company ran a battery-swap service for electric trucks in the 1910s. Parallel: every swap startup since.
- Lincoln Highway (1913): a private coast-to-coast route built on sponsorship before federal money. Parallel: privately funded corridors.
- 1930s gasoline price wars and the rise of branded stations. Parallel: the fast-charging price war.
- Railroad gauge standardization. Verified 2026-09-28 (Wikipedia, Track gauge in the United States): starting May 31, 1886, Southern railroads moved one rail 3 inches, from 5 ft to 4 ft 9 in, on about 14,000 miles of track in about 36 hours; inside spikes were pre-driven at the new gauge. Parallel: connector transition. Asked 2026-09-28, skipped as too abstract; reuse only with a simpler question.
- Telephone interconnection and long-distance access rules. Parallel: roaming and open networks.
- Early ATM networks (proprietary until shared networks won). Parallel: charging network interoperability.
- The quartz crisis (1970s to 1980s): cheap, accurate quartz watches nearly wiped out Swiss mechanical watchmaking, which survived by becoming a luxury product. Parallel: ICE cars as the niche, emotional purchase once EVs are the default. (Aatish's idea.)

## Essay prompt bank (rotate; mark used with a date)

- What I'd tell a hotel owner who got a charger pitch this week. (Used 2026-09-24.)
- The line in the pro forma everyone gets wrong. (Used 2026-09-24.)
- Uptime numbers: why 97% can mean a broken site. (Used 2026-09-28.)
- What a demand charge actually did to a real site (anonymized).
- Hardware is a commodity; installation is not. Where the money goes.
- The site host pitch that works and the one that doesn't.
- What I learned taking a charging company public, that an operator can use.
- NACS for site hosts: what to do with the chargers you already own.
- Level 2 is underrated. Or overrated. Pick one.
- The first 90 days after a charger goes live.
- Why fleet charging is a scheduling problem pretending to be a hardware problem.
- Grants are not free money: the strings that cost the most. (Close to the Colorado question he skipped 2026-09-28; wait a few weeks.)
- What "open source" means for a charging business.
- The worst question a customer ever asked me that turned out to be the right one.
- Pricing: per kWh, per minute, idle fees, and what drivers actually respond to.
- Where the next 5 years of charging margin comes from, if anywhere.

## Topic log (one line per post; newest first)

Schedule set 2026-09-28. Next open slot: Tue 2026-10-27.

- 2026-10-22 Thu essay (scheduled): Uptime says the charger is online. It doesn't say it works (his take: uptime means reporting; failures are POS/CMS/charger handoffs, pre-auth holds, port timeouts; measure first-time charge success, 80%+ is good). About 600 words; wants one anonymized story before it goes out.
- 2026-10-20 Tue essay (scheduled): Nobody gets ten sessions on day one (utilization ramp, with his one-a-week to two-to-three-a-day story over 2 to 2.5 years).
- 2026-10-15 Thu essay (scheduled): What I'd tell a hotel owner about a free charger (own it, don't sublease; finance it).
- 2026-10-13 Tue weekly (scheduled): Half the cables should still be CCS. Ionna's first NACS-only sites (his take: half the cables CCS until ~80% of new EVs have NACS); Tesla Semi volume production, 1.7 kWh/mile, 1.2 MW (his take: production isn't adoption); Colorado $23.2M for 270 ports at 35 sites (facts only).
- 2026-10-08 Thu weekly (scheduled): 2,500 electric semis ordered, zero chargers announced. ZET SCALE order (his take: chicken and egg, infrastructure cost vs diesel); California SB 969 / SB 1283 / AB 1820 (facts only); Cox August new EVs -46.9%, used +14.7% (facts only).
- 2026-10-06 Tue essay (scheduled, first post): Why I built The Charge Sheet.
- 2026-09-25 weekly (draft, not scheduled): fast-charging price war (Ionna, Walmart pricing), build-out outrunning utilization. Uses Paren Q1 numbers; Q2 is out. Refresh or retire.

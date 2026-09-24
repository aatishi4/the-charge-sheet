# The Charge Sheet

**A free, honest guide to the business of EV charging.** How charging works, what it really costs,
and whether it's worth doing, with real benchmark data from operating sites and planning tools you can use in a browser.

No sign-up, no sales pitch, no tracking cookies. Open source.

## What's inside

**Eight guides**, meant to be read in order or dipped into:

1. How charging works
2. The business
3. It's a real estate business
4. Paying for it
5. Batteries
6. Connectivity
7. Buying
8. Fleet charging

**Six tools:**

- **Site planner.** A ten-year pro forma for a charging site, with batteries, incentives, reliability, share links, CSV export and a printable one-pager.
- **Install cost estimator.** Wire sizing, conduit, trenching, gear and site work, priced by distance from the electrical room.
- **SBA loan check.** Loan size, payment and debt service coverage the way a lender sees it.
- **Fleet throughput.** Vehicles per day, the 80% rule, porter limits, and Level 2 against DC fast.
- **Utilization forecast.** Sessions per day from traffic or population, with a range instead of a single guess.
- **Connectivity check.** Grades cellular signal at the charger location and recommends a setup.

**Benchmarks** from real sites: session-level data from operating chargers, anonymized and cleaned. Not forecasts.

## Running it

`index.html` is the whole site and works on its own:

- Open `index.html` in a browser, or
- serve the folder locally, for example `python3 -m http.server`, then visit the address it prints.

The live site at chargesheet.io is built from it. `tools/build_pages.py` (Python 3, standard library only)
splits it into one page per guide and tool, each with its own URL, title, description, preview image
and structured data, and writes the result to `dist/`. Cloudflare Pages runs it on every push.
To preview the built site: `python3 tools/build_pages.py && python3 -m http.server -d dist`.

Page titles, descriptions and URLs live in the `PAGES` list at the top of `tools/build_pages.py`.
Preview images live in `og/` and are drawn by `tools/og_images.py` (needs Playwright).

Some live lookups (traffic counts, nearby stations, utility rates) call public APIs and need to be served over http, not opened as a file.

## Blog

Posts live in `posts/` as Markdown files named `YYYY-MM-DD-slug.md`, with a short header:

```
---
title: The headline
description: One or two sentences for search results and link previews.
date: 2026-10-06
tags: [demand charges, utilities]
kind: essay        # or weekly, for "The week in charging"
draft: true        # drafts only show on preview deployments, never on chargesheet.io
---
```

The build turns them into `/blog/`, `/blog/<slug>/` and an RSS feed at `/blog/feed.xml`, and adds the three newest to the home page.
Push a post to a branch other than `main` and Cloudflare gives you a preview at `<branch>.the-charge-sheet.pages.dev`, drafts included.
Remove `draft: true` and merge to `main` to publish. `python3 tools/og_images.py <slug>` draws the post's preview image.
To preview locally with drafts: `SHOW_DRAFTS=1 python3 tools/build_pages.py && python3 -m http.server -d dist`.

## Local data (optional)

`tools/build-data.mjs` downloads open charging-station and traffic-count data into `data/`, so lookups work offline.
Run it from the repository root with Node 18 or newer:

```
node tools/build-data.mjs --stations --state IL --nrel-key YOUR_KEY
node tools/build-data.mjs --aadt --state IL
```

See the comments at the top of the script for options.

## Project layout

```
index.html          The whole site: content, styles and tools
fonts/              Instrument Sans, self-hosted (SIL Open Font License)
img/                Author photos
data/               Optional local datasets, listed in data/manifest.json
tools/              build_pages.py (site build), blog.py (posts), spots.py (header illustrations),
                    og_images.py (preview images), build-data.mjs (data)
posts/              Blog posts, in Markdown
og/                 Link preview images, one per page
favicon.svg, favicon-32.png, apple-touch-icon.png, og-image.png
_headers            Caching and security headers for Cloudflare Pages
DEPLOY.md           How to put the site online
```

## Contributing

Corrections and anonymized site data are the most valuable things you can send. See `CONTRIBUTING.md`.

## License

Code: MIT. Written content, data and illustrations: CC BY 4.0. Details and exceptions in `LICENSE-CONTENT.md`.

## Disclaimer

Ballpark numbers for learning and early screening. Not engineering, financial, tax or legal advice.
A licensed electrician, engineer, lender and CPA should check anything you plan to build.

Built by [Aatish Patel](https://www.linkedin.com/in/aatish-patel-2b9424a4/).

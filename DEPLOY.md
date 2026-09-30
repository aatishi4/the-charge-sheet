# Putting The Charge Sheet online

About an hour, start to finish. Everything here is free except the domain (about $12 a year).

## 1. Put the code on GitHub

1. Sign in at github.com as **aatishi4**.
2. Create a new repository named **the-charge-sheet**. Make it **Public**. Don't add a README (this folder has one).
3. On the new repository page, choose **uploading an existing file**, then drag in **everything inside this folder**, including the `fonts`, `img`, `data` and `tools` folders. Commit.
4. In the repository's **Settings > General > Features**, turn on **Discussions**. The site's "Ask a question in public" button points there.

If you prefer the command line:

```
git init && git add . && git commit -m "Launch"
git branch -M main
git remote add origin https://github.com/aatishi4/the-charge-sheet.git
git push -u origin main
```

## 2. Host it on Cloudflare Pages

1. Create a free Cloudflare account.
2. Go to **Workers & Pages**, create an application, choose **Pages**, and connect your GitHub repository.
3. Build settings: framework preset **None**, build command **python3 tools/build_pages.py**, build output directory **dist**.
4. Deploy. You'll get an address like `the-charge-sheet.pages.dev`. Every push to GitHub redeploys automatically.

Alternative: GitHub Pages (repository Settings > Pages > deploy from the main branch). It works, but you lose Cloudflare's free cookie-free analytics and the `_headers` file.

## 3. Add your domain

1. Buy the domain. Cloudflare Registrar sells at cost, which keeps everything in one place.
2. In the Pages project, open **Custom domains** and add it. Cloudflare sets up the DNS and the certificate.

## 4. Replace the SITE_URL placeholders

Search for `SITE_URL` and replace it with your domain (for example `thechargesheet.com`) in:

- `index.html` (the link preview and canonical tags near the top),
- `robots.txt`,
- `sitemap.xml`.

Without this, LinkedIn won't show the preview image.

## 5. Turn on the contact form

1. Create a free account at formspree.io and a new form. Point it at the email you want messages sent to.
2. Copy the endpoint, which looks like `https://formspree.io/f/abcdwxyz`.
3. In `index.html`, find `formspree: ''` near the bottom and paste it between the quotes. Commit.

## 6. Turn on analytics

In the Cloudflare Pages project, open **Metrics** and enable **Web Analytics**. It's free, cookie-free, and needs no banner.

## 7. Check it before you share it

- Every page loads on a phone, and in dark mode.
- The contact form sends, and the message arrives.
- LinkedIn, GitHub and "Ask a question in public" links on the About page work.
- The live lookups work with free keys: traffic counts and nearby stations in the Utilization forecast (NREL key from developer.nlr.gov/signup), and utility rates in the Site planner (OpenEI key from openei.org). They have never been tested against the live APIs, so this is the first real run.
- Share links, spreadsheet downloads and the printable pro forma work in the planner.
- Paste your URL into LinkedIn's Post Inspector (linkedin.com/post-inspector) and confirm the preview image appears.

## 8. Before you announce it

- Launch after your last day at XCharge, and check any confidentiality or outside-activity terms from XCharge and Gotion.
- Ask two people to read it cold: one who knows nothing about charging, one who knows too much.

## Updating

Edit `index.html` on GitHub (the pencil icon) or locally, and commit. Cloudflare rebuilds the pages and redeploys in about a minute.
To change a page's search title, description or URL, edit `PAGES` in `tools/build_pages.py`. Changing a URL needs a redirect in the `_redirects` section of that script.
Review incentives, SBA rules and tariffs each quarter, and bump "Last updated" on the Method page.

## Search: what the build does for you

- **Titles and descriptions** live in `PAGES` and `HOME_PAGES` in `tools/build_pages.py`. Keep titles under 60 characters and descriptions under 160, or Google cuts them off.
- **Sitemap dates** come from the git history of `index.html`: each page's `lastmod` (and its `dateModified` in the structured data) is the last commit that changed that page's section, so editing one guide doesn't mark every page as new.
- **Empty blog**: until the first post is live, `/blog/` is `noindex` and left out of the sitemap. The first scheduled post flips it back on its own.
- **Other pages' content** on each page is hollowed out, and its headings and links are turned into plain elements, so every page has one H1 and no empty links.
- **Catalogs**: the charger catalog and the home gear page get a plain product list in the HTML, which the script replaces on load. Search engines see the products without running the script.
- **Data**: the charger catalog JSON goes only on the planner, catalog and report pages, and the home gear JSON only on home pages, at the end of the body.
- **`/llms.txt`** is a plain list of every page for AI search tools, built from the same `PAGES` list.
- **Share cards**: `python3 tools/og_images.py` (see the top of that file). Home-side cards: `python3 tools/og_images.py home-side`.

## 8. The home side (residential charging, batteries, V2H)

The home side lives in `index.html` between `<!--home-side-->` markers, with its data in `data/home-gear.json` and a small server function in `functions/api/rates.js`.

- **Previews** (any branch other than main) always include it, with `noindex` and nothing in the sitemap. Locally: `SHOW_HOME=1 python3 tools/build_pages.py`.
- **chargesheet.io** strips it until you set `HOME_LIVE = True` near the top of `tools/build_pages.py`. That one change adds the ten pages to the nav, the footer, the sitemap and search.
- **ZIP code rate lookup.** Works with no key. `tools/build_rates.py` builds `data/rates/` from two free datasets (EIA Form 861 ZIP-to-utility averages and the OpenEI Utility Rate Database bulk download), and the calculator reads those static files. `.github/workflows/refresh-rates.yml` rebuilds them every Monday (committing only when the data changes), or run it by hand from the Actions tab. If the OpenEI download is down, it keeps the last good plans and still refreshes the ZIP map and EIA averages. Optional: add an `OPENEI_KEY` secret in Cloudflare (**Workers & Pages > the-charge-sheet > Settings > Variables and Secrets**, Production and Preview) and the calculator asks the live OpenEI API first, falling back to the static files.
- **Adding a product.** Append a record to the right list in `data/home-gear.json` (copy the closest one). Chargers, batteries and vehicles show up in the gear page and the tools with no code changes.
- **Gas and electricity prices.** `data/fuel-prices.json` holds EIA weekly gasoline prices (regular and premium, U.S., regions and the states EIA publishes), EIA monthly residential electricity prices by state, and Paren's quarterly U.S. average for public DC fast charging. Get a free EIA key at eia.gov/opendata/register.php and save it as the GitHub repository secret `EIA_API_KEY`. The "Refresh fuel and electricity prices" workflow then updates the file every Tuesday. Without the key it does nothing and the seeded numbers stay. Update the `dcfc` block by hand when Paren publishes a new quarter.
- **Gas cars.** The comparison list is `gasCars` in `data/home-gear.json` (EPA combined mpg, regular or premium). Each EV's `twin` picks its default gas match.

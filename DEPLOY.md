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

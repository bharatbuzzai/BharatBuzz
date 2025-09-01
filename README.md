# BharatBuzz AI — Modular Twitter news aggregator (free HF model)

## What this repo does
- Scrapes a set of Indian news RSS feeds.
- Detects trending topic across sources, fetches the articles, summarizes into a short 2-line summary using Hugging Face summarizer (free).
- Downloads one representative image (from the article), writes a `docs/<slug>.md` blog post and saves the image to `docs/images/`.
- Tweets the summary + image every 2 hours (and can be manually triggered).

## Quick setup
1. Copy the repo files (this project structure).
2. Add GitHub secrets (Settings → Secrets & variables → Actions):
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET`
   - `TWITTER_ACCESS_TOKEN`
   - `TWITTER_ACCESS_SECRET`
   - Optional: `BLOG_BASE_URL` (default used if absent).
3. In GitHub Repo → Settings → Pages:
   - Source: `main` branch → `/docs` folder → Save
4. Trigger the workflow (Actions → `BharatBuzz AI Automation` → Run workflow) or wait 2 hours for schedule.
5. Watch Actions logs — they are verbose and point to failing step.

## Notes
- First run will download the summarization model (can take a minute).
- All generated blog posts and images go to `docs/` and `docs/images/` (so GitHub Pages can serve them).
- All modules are separate and easily replaceable.


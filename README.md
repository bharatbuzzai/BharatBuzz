# BharatBuzz AI

Free, automated Indian news aggregation → AI summary → GitHub Pages blog → auto-tweet.

## How it works
1. Pulls RSS from 20+ Indian sources (last 90 minutes).
2. Clusters similar headlines; picks the most cross-reported story.
3. Scrapes 2–3 articles, extracts text + an image.
4. Summarizes with a free HuggingFace model (DistilBART).
5. Publishes to GitHub Pages (`docs/*.md`).
6. Tweets title + blog link (+ image if available).

## Secrets needed (GitHub → Settings → Secrets and variables → Actions)
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

Optional:
- `BLOG_BASE_URL` (default `https://<your-username>.github.io/<repo>`)

## Run
- Manual: Actions → “BharatBuzz AI” → Run workflow
- Scheduled: every 2 hours (UTC) by default

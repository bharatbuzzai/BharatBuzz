"""
Entry point for the pipeline.
Run with: python -m bharatbuzz.run
"""

from .logger import log
from .feeds import get_feeds
from .fetch import fetch_recent_entries, fetch_article_text_and_image, download_image
from .cluster import cluster_and_pick_trend
from .summarize import summarize
from .blog_writer import save_blog
from .twitter_client import post_tweet_with_media
from .config import AGG_WINDOW_MINUTES, BLOG_BASE_URL, IMAGES_DIR, SUMMARY_WORDS, BLOG_TITLE_MAX

from datetime import datetime, timezone

def run():
    log("=" * 60)
    log("BharatBuzz pipeline start")

    feeds = get_feeds()

    log("STEP 1: Fetch recent entries")
    recent = fetch_recent_entries(feeds, window_minutes=AGG_WINDOW_MINUTES)
    if not recent:
        log("No recent items. Exiting.")
        return False
    log(f"Collected {len(recent)} recent items")

    log("STEP 2: Cluster & pick trend")
    stories = cluster_and_pick_trend(recent)
    if not stories:
        log("No stories selected. Exiting.")
        return False
    log(f"Chosen {len(stories)} article(s): " + ", ".join(s['source'] for s in stories))

    log("STEP 3: Fetch article text & cover image (from top sources)")
    texts = []
    cover_url = None
    for s in stories:
        txt, img = fetch_article_text_and_image(s["link"])
        if txt:
            texts.append(txt)
        if not cover_url and img:
            cover_url = img

    if not texts:
        log("No article texts extracted. Exiting.")
        return False

    long_text = " ".join(texts)[:8000]

    log("STEP 4: Summarize")
    final_summary = summarize(long_text, max_words=SUMMARY_WORDS)
    if not final_summary:
        log("Summarization returned empty text. Exiting.")
        return False

    # Create headline (two-line summary): take first two sentences or first 25 words
    sentences = [s.strip() for s in final_summary.split(".") if s.strip()]
    two_lines = None
    if len(sentences) >= 2:
        two_lines = sentences[0] + ". " + sentences[1] + "."
    else:
        # as fallback, use first ~25 words
        two_lines = " ".join(final_summary.split()[:25]) + ("..." if len(final_summary.split()) > 25 else "")

    headline = sentences[0] if sentences else two_lines
    if len(headline) < 10:
        headline = stories[0]["title"]

    headline = headline[:BLOG_TITLE_MAX].rstrip(" ,.;-")

    # slug and image
    slug = None
    image_path = None
    if cover_url:
        slug = headline.replace(" ", "-")[:60]
        image_path = download_image(cover_url, slug)

    # Save blog
    blog_path = save_blog(headline, final_summary, stories, image_path=image_path)

    # Tweet: summary (two lines) + hashtags (picked naively from headline)
    hashtags = "#BharatBuzzAI #IndiaNews"
    tweet_text = f"{two_lines}\n\n{hashtags}"
    # Optionally include link to blog (uncomment to send link)
    # public_blog_url = f"{BLOG_BASE_URL}/{slug}.html" if slug else ""
    # tweet_text = f"{two_lines}\n\nRead: {public_blog_url}\n\n{hashtags}"

    log("STEP 5: Post Tweet")
    posted = post_tweet_with_media(tweet_text, image_path)
    if not posted:
        log("Tweet failed (logged above); pipeline ends with failure.")
        return False

    log("Pipeline completed successfully.")
    return True

if __name__ == "__main__":
    ok = run()
    if not ok:
        raise SystemExit(1)

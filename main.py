import os
import time
from feeds import FEEDS
from summarizer import summarize_headlines
from fetcher import (
    ensure_dirs, fetch_headlines, pick_best_cluster,
    fetch_article_image, download_image_to_images
)
from twitter_client import post_tweet_with_image

# Configuration
PER_FEED = 3     # headlines per feed
MIN_SOURCES = 2  # minimum distinct sources for trending cluster

def run_once():
    print("STEP 1: Collecting headlines...")
    items = fetch_headlines(FEEDS, per_feed=PER_FEED)
    if not items:
        print("No headlines found.")
        return

    print(f"Collected {len(items)} items. Finding best cluster...")
    cluster = pick_best_cluster(items, min_sources=MIN_SOURCES)
    if not cluster:
        print("No strong cluster found.")
        return

    # Gather cluster titles
    titles = [c["title"] for c in cluster][:25]
    print("Cluster titles sample:", titles[:5])

    # Summarize into one headline
    summary = summarize_headlines(titles, max_words=20)
    if not summary:
        summary = titles[0] if titles else "Breaking News"

    # Try to fetch an image from one article in cluster
    img_path = ""
    for c in cluster:
        img_url = fetch_article_image(c["link"])
        if img_url:
            img_path = download_image_to_images(
                img_url,
                slug_seed=c["title"][:30].replace(" ", "-")
            )
            if img_path:
                break

    print("Image saved at:", img_path if img_path else "none")

    # Prepare tweet text (no blog link, only summary)
    tweet_text = summary.strip()[:280]

    print("STEP 2: Posting tweet...")
    ok = post_tweet_with_image(tweet_text, img_path)
    if not ok:
        print("❌ Tweet failed. Check credentials/permissions.")
    else:
        print("✅ Tweet succeeded.")

if __name__ == "__main__":
    run_once()

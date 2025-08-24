import os
from datetime import datetime
from bharatbuzz.logger import log, log_error, log_section
from bharatbuzz.config import BLOG_BASE_URL, DOCS_DIR, IMAGES_DIR, BLOG_TITLE_MAX
from bharatbuzz.fetch import fetch_recent_entries, fetch_article_text_and_image, download_image, ensure_dirs as ensure_fetch_dirs
from bharatbuzz.cluster import cluster_and_pick_trend
from bharatbuzz.summarize import summarize
from bharatbuzz.blog import ensure_dirs as ensure_blog_dirs, build_slug, write_markdown, pick_hashtags
from bharatbuzz.twitter_client import post_tweet

def main():
    try:
        log_section("STEP 1: Prepare folders")
        ensure_fetch_dirs()
        ensure_blog_dirs()

        log_section("STEP 2: Fetch recent RSS items")
        recent = fetch_recent_entries()
        if not recent:
            log("No recent items. EXIT.")
            return

        log_section("STEP 3: Cluster & pick trending story")
        stories = cluster_and_pick_trend(recent)
        if not stories:
            log("No trend chosen. EXIT.")
            return

        log_section("STEP 4: Fetch article texts & pick cover image")
        texts = []
        cover_img_url = None
        for s in stories:
            txt, img = fetch_article_text_and_image(s["link"])
            if txt:
                texts.append(txt)
            if not cover_img_url and img:
                cover_img_url = img

        long_text = " ".join(texts) if texts else ". ".join([s["title"] for s in stories])
        if len(long_text) > 8000:
            long_text = long_text[:8000]

        log_section("STEP 5: Summarize")
        final_summary = summarize(long_text)

        title = (final_summary.split(".")[0] or stories[0]["title"]).strip()
        if len(title) < 20:
            title = stories[0]["title"]
        title = title[:BLOG_TITLE_MAX].rstrip(" ,.;-")

        slug = build_slug(title)
        image_rel = None
        if cover_img_url:
            out_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
            if download_image(cover_img_url, out_path):
                image_rel = f"/{IMAGES_DIR}/{os.path.basename(out_path)}"

        log_section("STEP 6: Write blog post")
        sources = [{"source": s["source"], "link": s["link"]} for s in stories]
        md_path = write_markdown(slug=slug, title=title, summary=final_summary, image_rel=image_rel, sources=sources)

        blog_url = BLOG_BASE_URL.rstrip("/") + f"/{slug}.html" if BLOG_BASE_URL else f"/{DOCS_DIR}/{slug}.md"
        tweet_text = f"{title}\n\nRead: {blog_url}\n{pick_hashtags(title)}"

        log_section("STEP 7: Tweet it")
        posted = post_tweet(tweet_text, md_path.replace(".md", ".jpg") if image_rel else None)
        if not posted:
            log("Tweet not posted (check Twitter app permissions / tokens).")

        log("DONE.")

    except Exception as e:
        log_error("MAIN", e)

if __name__ == "__main__":
    main()

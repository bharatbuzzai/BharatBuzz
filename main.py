import os
import re
import io
import time
import json
import math
import html
import uuid
import glob
import tweepy
import torch
import feedparser
import requests
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from transformers import pipeline
from dateutil import parser as dateparser

# -------------------------
# CONFIG
# -------------------------
# 20 solid Indian news feeds (mix of national + business)
RSS_FEEDS = [
    "https://indianexpress.com/feed/",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-top-stories?format=xml",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "https://www.livemint.com/rss/news",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.deccanherald.com/rss.xml",
    "https://www.indiatoday.in/rss/1206578",
    "https://www.news18.com/rss/india.xml",
    "https://economictimes.indiatimes.com/feeds/newsdefault.cms",
    "https://www.firstpost.com/feed/",
    "https://www.indiatvnews.com/rss/india.xml",
    "https://www.business-standard.com/rss/latest.rss",
    "https://www.financialexpress.com/feed/",
    "https://www.deccanchronicle.com/rss_feed",
    "https://www.newindianexpress.com/Nation/rssfeed/?id=170&getXmlFeed=true",
    "https://www.tribuneindia.com/rss/feed?catId=1",
    "https://www.dnaindia.com/feeds/india.xml",
    "https://www.oneindia.com/rss/oneindia-india-fb.xml",
    "https://www.bbc.com/news/world/asia/india/rss.xml",
]

AGG_WINDOW_MINUTES = 90       # consider items published in last 60–90 minutes
MIN_SOURCES_FOR_TREND = 2     # must appear in at least 2 sources to count as a trend
MAX_ARTICLES_TO_MERGE = 3     # fetch full text from up to 3 sources for the blog
SUMMARY_WORDS = 160           # final blog summary length (approx)
BLOG_TITLE_MAX = 110          # for tweet title

# blog & images output
DOCS_DIR = "docs"
IMAGES_DIR = "images"

# Build your GitHub Pages base URL (update if different)
# Example for: user "bharatbuzzai" and repo "BharatBuzz"
BLOG_BASE_URL = os.getenv("BLOG_BASE_URL", "https://bharatbuzzai.github.io/BharatBuzz")

# Twitter credentials via GitHub Secrets
TW_KEY    = os.getenv("TWITTER_API_KEY")
TW_SECRET = os.getenv("TWITTER_API_SECRET")
TW_ATOK   = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ASEC   = os.getenv("TWITTER_ACCESS_SECRET")

# -------------------------
# Helpers
# -------------------------
def ensure_dirs():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = BeautifulSoup(s, "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_pubdate(e):
    # Try typical fields: published, updated, etc.
    dt = None
    for k in ["published", "updated", "pubDate", "dc:date"]:
        if getattr(e, k, None):
            try:
                dt = dateparser.parse(getattr(e, k))
                break
            except Exception:
                pass
    if not dt:
        # feedparser sometimes provides .published_parsed
        pp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        if pp:
            try:
                dt = datetime(*pp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return dt

STOPWORDS = set("""
a an the of for on in and or at to with from by about into over under across up down off out as is be will would could should
this that these those here there where when how why which who whom whose are were been being have has had do does did not
""".split())

def norm_title(title: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
    words = [w for w in t.split() if len(w) >= 4 and w not in STOPWORDS]
    words = sorted(set(words))
    return " ".join(words[:10])  # trim to top 10 tokens for key stability

def fetch_article_text_and_image(url: str):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return "", None
        soup = BeautifulSoup(r.text, "html.parser")
        # Find og:image
        img_url = None
        for prop in ["og:image", "twitter:image"]:
            tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                img_url = tag["content"].strip()
                break
        # Article text: try common containers
        text_blocks = []
        for sel in ["article", "div[itemprop='articleBody']", "div[class*='article']",
                    "div[class*='content']", "section", "main"]:
            cont = soup.select_one(sel)
            if cont:
                ps = cont.find_all("p")
                if len(ps) > 3:
                    text_blocks = [p.get_text(" ", strip=True) for p in ps]
                    break
        if not text_blocks:
            # fallback: all paragraphs
            ps = soup.find_all("p")
            text_blocks = [p.get_text(" ", strip=True) for p in ps[:12]]
        full_text = clean_text(" ".join(text_blocks))
        return full_text, img_url
    except Exception:
        return "", None

def download_image(url: str, slug: str):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=12)
        if r.status_code != 200:
            return None
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
        im.save(path, format="JPEG", quality=88)
        return path
    except Exception:
        return None

def build_slug(title: str):
    t = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip())[:80].strip("-")
    return t + "-" + uuid.uuid4().hex[:6]

def pick_hashtags(title: str):
    kw = [w for w in re.findall(r"[A-Za-z]{4,}", title) if w.lower() not in STOPWORDS]
    kw = kw[:3]
    tags = ["#BharatBuzzAI", "#IndiaNews"]
    tags += [f"#{w.title()}" for w in kw[:2]]
    return " ".join(tags)

# -------------------------
# MODEL (Hugging Face)
# -------------------------
# Faster summarizer for CPU
SUMM = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize(text: str, max_words=SUMMARY_WORDS):
    if not text or len(text.split()) < 30:
        return text
    # 1 word ~1.3 tokens approx; set max_length conservatively for CPU
    max_len = min(220, int(max_words * 1.3))
    result = SUMM(text, max_length=max_len, min_length=80, do_sample=False)
    return result[0]["summary_text"]

# -------------------------
# TWITTER
# -------------------------
def get_twitter_clients():
    api_v1 = None
    if all([TW_KEY, TW_SECRET, TW_ATOK, TW_ASEC]):
        auth = tweepy.OAuth1UserHandler(TW_KEY, TW_SECRET)
        auth.set_access_token(TW_ATOK, TW_ASEC)
        api_v1 = tweepy.API(auth)
    return api_v1

def post_tweet_with_media(text: str, media_path: str = None):
    api_v1 = get_twitter_clients()
    if not api_v1:
        print("⚠️ Twitter credentials missing.")
        return False
    try:
        if media_path and os.path.exists(media_path):
            api_v1.update_status_with_media(status=text[:280], filename=media_path)
        else:
            api_v1.update_status(status=text[:280])
        print("✅ Tweet posted.")
        return True
    except Exception as e:
        print("❌ Tweet failed:", e)
        return False

# -------------------------
# PIPELINE
# -------------------------
def fetch_recent_entries():
    recent = []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=AGG_WINDOW_MINUTES)

    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed)
            for e in parsed.entries[:6]:
                title = clean_text(getattr(e, "title", ""))
                link  = getattr(e, "link", "")
                if not title or not link:
                    continue
                dt = parse_pubdate(e)
                if dt and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if not dt or dt < cutoff:
                    continue
                recent.append({
                    "title": title,
                    "link": link,
                    "source": parsed.feed.get("title", feed),
                    "published": dt,
                    "norm": norm_title(title),
                })
        except Exception as ex:
            print("RSS error:", feed, ex)
    return recent

def cluster_and_pick_trend(recent):
    if not recent:
        return None
    groups = {}
    for item in recent:
        key = item["norm"]
        groups.setdefault(key, []).append(item)

    # score by number of distinct sources (prefer more sources, then most recent)
    best_key = None
    best_score = (-1, datetime.min.replace(tzinfo=timezone.utc))
    for k, items in groups.items():
        sources = set(i["source"] for i in items)
        latest = max(i["published"] for i in items)
        score = (len(sources), latest)
        if score > best_score:
            best_score = score
            best_key = k

    chosen = groups[best_key]
    distinct_sources = set(i["source"] for i in chosen)
    if len(distinct_sources) < MIN_SOURCES_FOR_TREND:
        print("No multi-source trend found; falling back to the freshest story.")
        chosen = [max(recent, key=lambda x: x["published"])]

    # Deduplicate by link
    uniq = []
    seen = set()
    for i in chosen:
        if i["link"] not in seen:
            uniq.append(i)
            seen.add(i["link"])
    return uniq[:MAX_ARTICLES_TO_MERGE]

def build_blog_and_tweet(stories):
    # Merge text from stories
    texts = []
    image_path = None
    cover_url = None
    for s in stories:
        txt, img = fetch_article_text_and_image(s["link"])
        if txt:
            texts.append(txt)
        if not cover_url and img:
            cover_url = img

    long_text = " ".join(texts)
    if len(long_text) > 8000:
        long_text = long_text[:8000]

    if not long_text:
        # fallback: concatenate titles
        long_text = ". ".join([s["title"] for s in stories])

    final_summary = summarize(long_text, max_words=SUMMARY_WORDS)
    # Title = first sentence of summary (or aggregated title)
    title = final_summary.split(".")[0]
    if len(title) < 20:
        title = stories[0]["title"]
    title = title[:BLOG_TITLE_MAX].rstrip(" ,.;-")  # constrain for tweet

    slug = build_slug(title)
    if cover_url:
        image_path = download_image(cover_url, slug)

    # Build blog content
    lines = []
    lines.append(f"# {title}\n")
    lines.append(f"*Published:* {datetime.now().strftime('%d %B %Y, %H:%M %Z')}\n")
    if image_path:
        rel_img = f"/{os.path.basename(IMAGES_DIR)}/{os.path.basename(image_path)}"
        lines.append(f"![cover]({rel_img})\n")
    lines.append(final_summary + "\n\n")
    lines.append("**Sources:**\n")
    for s in stories:
        lines.append(f"- [{s['source']}]({s['link']})")

    ensure_dirs()
    blog_path = os.path.join(DOCS_DIR, f"{slug}.md")
    with open(blog_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    blog_url = f"{BLOG_BASE_URL}/{slug}.html"  # GH Pages converts .md → .html
    tweet_text = f"{title}\n\nRead: {blog_url}\n{pick_hashtags(title)}"
    return blog_path, image_path, tweet_text

def main():
    ensure_dirs()
    recent = fetch_recent_entries()
    if not recent:
        print("No recent items.")
        return

    stories = cluster_and_pick_trend(recent)
    if not stories:
        print("No trend chosen.")
        return

    blog_path, image_path, tweet_text = build_blog_and_tweet(stories)
    print("Blog file:", blog_path)
    print("Tweet:", tweet_text)
    # Post tweet (with image if available)
    post_tweet_with_media(tweet_text, image_path)

if __name__ == "__main__":
    main()


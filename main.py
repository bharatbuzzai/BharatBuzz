import os
import re
import html
import time
import tweepy
import feedparser
from bs4 import BeautifulSoup

# -------------------------
# Twitter credentials (from GitHub Actions env)
# -------------------------
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# -------------------------
# Configure Tweepy (try v2, fallback to v1.1)
# -------------------------
client = None
api_v1 = None

try:
    # v2 client (preferred)
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET,
        wait_on_rate_limit=True,
    )
except Exception as e:
    print("⚠️ Could not init Tweepy v2 client:", e)

try:
    # v1.1 fallback
    auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    api_v1 = tweepy.API(auth)
except Exception as e:
    print("⚠️ Could not init Tweepy v1.1 API:", e)

# -------------------------
# RSS feeds (public)
# -------------------------
RSS_FEEDS = [
    "https://indianexpress.com/feed/",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-top-stories?format=xml",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "https://www.livemint.com/rss/news",
]

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = BeautifulSoup(s, "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def summarize(headline: str, description: str) -> str:
    # Take headline + first sentence of description
    desc = clean_text(description)
    if "." in desc:
        desc = desc.split(".")[0]
    text = f"{clean_text(headline)} – {desc}".strip(" –")
    return text

def pick_latest_entry(entries):
    # entries already sorted by feedparser typically; just take the first valid
    for e in entries:
        title = clean_text(getattr(e, "title", "")) or ""
        link  = getattr(e, "link", "") or ""
        if not title or not link:
            continue
        # Skip live blogs & videos
        bad = ["live blog", "live updates", "video:", "watch:"]
        if any(b.lower() in title.lower() for b in bad):
            continue
        return {"title": title, "link": link, "summary": clean_text(getattr(e, "summary", ""))}
    return None

def fetch_top_story():
    all_entries = []
    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed)
            if parsed.entries:
                all_entries.extend(parsed.entries[:5])  # take a few from each
        except Exception as e:
            print(f"⚠️ RSS error {feed}: {e}")

    if not all_entries:
        print("No entries found from RSS.")
        return None

    top = pick_latest_entry(all_entries)
    return top

def compose_tweet(item):
    headline = item["title"]
    url = item["link"]
    summary = summarize(headline, item.get("summary", ""))

    tweet = f"{summary}\n\nRead: {url}\n#BharatBuzzAI #IndiaNews"
    if len(tweet) > 280:
        # Trim carefully
        excess = len(tweet) - 280
        summary_trimmed = summary[:-excess-3].rstrip() + "..."
        tweet = f"{summary_trimmed}\n\nRead: {url}\n#BharatBuzzAI #IndiaNews"
    return tweet

def post_tweet(text):
    # Try v2 first
    if client:
        try:
            client.create_tweet(text=text)
            print("✅ Tweeted via v2.")
            return True
        except Exception as e:
            print("⚠️ v2 create_tweet failed:", e)

    # Fallback to v1.1
    if api_v1:
        try:
            api_v1.update_status(status=text)
            print("✅ Tweeted via v1.1.")
            return True
        except Exception as e:
            print("⚠️ v1.1 update_status failed:", e)

    print("❌ Could not tweet (permissions or tokens may be wrong).")
    return False

if __name__ == "__main__":
    item = fetch_top_story()
    if not item:
        print("No story to tweet.")
    else:
        tweet = compose_tweet(item)
        print("Draft tweet:\n", tweet)
        posted = post_tweet(tweet)
        if posted:
            print("Done.")
        else:
            print("Tweet failed.")


import os
import re
import html
import time
import tweepy
import feedparser
from bs4 import BeautifulSoup
import openai
from datetime import datetime

# -------------------------
# Twitter credentials
# -------------------------
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# -------------------------
# Configure Tweepy
# -------------------------
client = None
api_v1 = None
try:
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
    auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    api_v1 = tweepy.API(auth)
except Exception as e:
    print("⚠️ Could not init Tweepy v1.1 API:", e)

# -------------------------
# RSS feeds (10+ Indian sources)
# -------------------------
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
]

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = BeautifulSoup(s, "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fetch_multiple_headlines(limit=20):
    """Fetch top headlines from all feeds"""
    headlines = []
    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed)
            for e in parsed.entries[:2]:  # top 2 per source
                title = clean_text(getattr(e, "title", ""))
                link = getattr(e, "link", "")
                if title and link and len(title) > 25:
                    headlines.append(f"{title} ({link})")
        except Exception as e:
            print(f"⚠️ RSS error {feed}: {e}")
    return headlines[:limit]

def summarize_with_ai(headlines):
    if not headlines:
        return None
    prompt = f"""
    You are BharatBuzz AI, an Indian news summarizer.
    Summarize these headlines into ONE clear news article (150 words max).
    Remove repetition, merge context, and keep neutral tone.

    Headlines:
    {chr(10).join(headlines)}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"system","content":"You summarize news for BharatBuzz AI."},
                      {"role":"user","content":prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("⚠️ OpenAI summarization failed:", e)
        return None

def save_blog(summary):
    if not summary:
        return None
    filename = f"news_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# BharatBuzz AI Daily News ({datetime.now().strftime('%d %B %Y')})\n\n")
        f.write(summary)
    return filename

def compose_tweet(summary_file, summary_text):
    blog_url = f"https://bharatbuzzai.github.io/{summary_file}"
    headline = summary_text.split(".")[0]  # take first sentence
    tweet = f"{headline}...\n\nRead full: {blog_url}\n#BharatBuzzAI #IndiaNews"
    return tweet[:280]

def post_tweet(text):
    if client:
        try:
            client.create_tweet(text=text)
            print("✅ Tweeted via v2.")
            return True
        except Exception as e:
            print("⚠️ v2 create_tweet failed:", e)
    if api_v1:
        try:
            api_v1.update_status(status=text)
            print("✅ Tweeted via v1.1.")
            return True
        except Exception as e:
            print("⚠️ v1.1 update_status failed:", e)
    return False

if __name__ == "__main__":
    headlines = fetch_multiple_headlines()
    summary = summarize_with_ai(headlines)
    if not summary:
        print("No summary generated.")
    else:
        blog_file = save_blog(summary)
        tweet = compose_tweet(blog_file, summary)
        post_tweet(tweet)



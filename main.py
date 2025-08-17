import os
import requests
import tweepy
import feedparser
from bs4 import BeautifulSoup
import textwrap

# ======================
# API KEYS FROM SECRETS
# ======================
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# ======================
# TWITTER AUTH
# ======================
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
twitter = tweepy.API(auth)

# ======================
# FETCH NEWS
# ======================
def fetch_news():
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "articles" not in data:
        return []
    return data["articles"]

# ======================
# SIMPLE SUMMARIZER
# ======================
def summarize(text):
    # very basic summary: take first 2 sentences
    text = text.strip().replace("\n", " ")
    parts = text.split(". ")
    return ". ".join(parts[:2]) + "."

# ======================
# TWEET NEWS
# ======================
def post_to_twitter(headline, url):
    tweet = f"{headline}\n\nRead more: {url}\n\n#BharatBuzzAI #IndiaNews"
    if len(tweet) > 280:
        tweet = tweet[:276] + "..."
    twitter.update_status(tweet)
    print("✅ Tweeted:", headline)

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    articles = fetch_news()
    if not articles:
        print("No news fetched.")
    else:
        for art in articles[:1]:   # only 1 article per run (every hour)
            headline = art.get("title", "")
            description = art.get("description", "")
            url = art.get("url", "")
            content = headline + " " + description

            summary = summarize(content)
            post_to_twitter(summary, url)

import os
import requests
from bs4 import BeautifulSoup
import schedule
import time
import tweepy
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

# Twitter API keys
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# Scrape function
def fetch_latest_news():
    url = "https://www.thehindu.com/news/national/"  # Example news source
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract first article
    article = soup.find("a", class_="story-card75x1-text")  
    if not article:
        return None, None

    title = article.get_text(strip=True)
    link = article["href"]

    # Fetch image from article
    img_url = None
    article_page = requests.get(link)
    article_soup = BeautifulSoup(article_page.text, "html.parser")
    img_tag = article_soup.find("img")
    if img_tag and img_tag.get("src"):
        img_url = img_tag["src"]

    return title, img_url

# Tweet function
def post_tweet():
    title, img_url = fetch_latest_news()
    if not title:
        print("No news found.")
        return

    try:
        if img_url:
            img_data = requests.get(img_url).content
            filename = "temp.jpg"
            with open(filename, "wb") as f:
                f.write(img_data)
            api.update_status_with_media(status=title[:270], filename=filename)
            os.remove(filename)
            print(f"Tweeted with image: {title}")
        else:
            api.update_status(status=title[:280])
            print(f"Tweeted (text only): {title}")
    except Exception as e:
        print(f"Error posting tweet: {e}")

# Scheduler (every 2 hours)
schedule.every(2).hours.do(post_tweet)

print("Bot running... tweets will be posted every 2 hours.")

while True:
    schedule.run_pending()
    time.sleep(60)


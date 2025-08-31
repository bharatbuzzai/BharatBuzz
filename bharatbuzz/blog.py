import os
import tweepy
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random

# ===============================
#  Twitter Authentication
# ===============================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# ===============================
#  News Scraper
# ===============================
def scrape_news():
    url = "https://www.indiatoday.in/news"  # Example news source
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    headlines = []
    for item in soup.select("h2, h3"):
        text = item.get_text(strip=True)
        if text and len(text.split()) > 5:
            headlines.append(text)
    return headlines[:5]  # take top 5 headlines

# ===============================
#  Generate Blog Content
# ===============================
def generate_blog(headlines):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    blog_title = f"📰 BharatBuzz AI News Update ({now})"
    blog_content = "Here are the top trending news updates in India:\n\n"
    for i, headline in enumerate(headlines, 1):
        blog_content += f"{i}. {headline}\n"
    return blog_title, blog_content

# ===============================
#  Save Blog Locally
# ===============================
def save_blog(title, content):
    filename = f"blog_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{content}")
    return filename

# ===============================
#  Tweet with Headline + Blog Link
# ===============================
def tweet_news(headlines, blog_link):
    headline = random.choice(headlines)  # pick a random headline
    tweet_text = f"📰 {headline}\n\nRead full update here: {blog_link}"
    
    # Post tweet
    api.update_status(tweet_text)
    print("✅ Tweet posted:", tweet_text)

# ===============================
#  Main
# ===============================
if __name__ == "__main__":
    headlines = scrape_news()
    if not headlines:
        print("⚠️ No headlines found!")
        exit()

    title, content = generate_blog(headlines)
    blog_file = save_blog(title, content)

    # Simulate blog link (later you can host on GitHub Pages or Notion API)
    blog_link = f"https://bharatbuzzai.github.io/blogs/{blog_file}"

    tweet_news(headlines, blog_link)


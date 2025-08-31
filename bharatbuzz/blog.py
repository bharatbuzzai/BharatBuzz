import os
import requests
import tweepy
from datetime import datetime

# --- Twitter Auth ---
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
)
twitter_client = tweepy.API(auth)

# --- Blog Path ---
BLOG_DIR = "blogs"
os.makedirs(BLOG_DIR, exist_ok=True)

def fetch_news():
    """Dummy example - replace with real scraper later"""
    return {
        "headline": "Government announces new digital policy",
        "summary": "The Indian government has introduced a new digital policy focusing on AI, cybersecurity, and digital infrastructure...",
        "image_url": "https://example.com/sample.jpg"
    }

def save_blog(news):
    """Save blog post as markdown"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{BLOG_DIR}/post_{timestamp}.md"
    blog_content = f"# {news['headline']}\n\n{news['summary']}\n\nPublished: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(blog_content)
    return filename

def download_image(url):
    """Download image locally for Twitter"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            path = "temp.jpg"
            with open(path, "wb") as f:
                f.write(response.content)
            return path
    except Exception as e:
        print("Image download failed:", e)
    return None

def tweet(news, blog_link):
    """Post tweet with link + optional image"""
    tweet_text = f"{news['headline']}\n\nRead more: {blog_link}"
    image_path = download_image(news.get("image_url", ""))
    
    try:
        if image_path:
            twitter_client.update_status_with_media(tweet_text, image_path)
        else:
            twitter_client.update_status(status=tweet_text)
        print("✅ Tweet posted successfully!")
    except Exception as e:
        print("❌ Tweet failed:", e)

def main():
    news = fetch_news()
    blog_file = save_blog(news)
    blog_link = f"https://yourgithubusername.github.io/{os.path.basename(blog_file)}"  # Change to your hosting link
    tweet(news, blog_link)

if __name__ == "__main__":
    main()


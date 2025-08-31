import os
import requests
import random
import tweepy
from bs4 import BeautifulSoup
from transformers import pipeline
from datetime import datetime

# ---------------- CONFIG ---------------- #
NEWS_SITES = [
    "https://www.indiatoday.in",
    "https://timesofindia.indiatimes.com",
    "https://www.ndtv.com",
    "https://www.thehindu.com"
]

BLOG_DIR = "blogs"
os.makedirs(BLOG_DIR, exist_ok=True)

# Load AI summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ---------------- SCRAPE FUNCTION ---------------- #
def scrape_articles():
    articles = []
    images = []

    for site in NEWS_SITES:
        try:
            html = requests.get(site, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")

            # find headlines
            links = soup.find_all("a", href=True)[:10]
            for link in links:
                title = link.get_text().strip()
                if len(title.split()) > 5:
                    url = link["href"]
                    if not url.startswith("http"):
                        url = site + url
                    articles.append({"title": title, "url": url})

                    # try image
                    img = soup.find("img")
                    if img and img.get("src"):
                        images.append(img["src"])
        except Exception as e:
            print(f"Error scraping {site}: {e}")
            continue

    return articles, images

# ---------------- SUMMARY FUNCTION ---------------- #
def summarize_articles(articles):
    if not articles:
        return None, None

    combined_text = " ".join([a["title"] for a in articles[:5]])
    summary = summarizer(combined_text, max_length=40, min_length=10, do_sample=False)[0]['summary_text']

    headline = summary.strip()
    return headline, summary

# ---------------- SAVE BLOG ---------------- #
def save_blog(headline, summary, articles):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(BLOG_DIR, f"{now}.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {headline}\n\n")
        f.write(f"**Summary:** {summary}\n\n")
        f.write("### Sources:\n")
        for a in articles[:5]:
            f.write(f"- [{a['title']}]({a['url']})\n")
    return filename

# ---------------- TWEET FUNCTION ---------------- #
def post_tweet(headline, blog_file, images):
    # Twitter Auth
    auth = tweepy.OAuth1UserHandler(
        os.getenv("TWITTER_API_KEY"),
        os.getenv("TWITTER_API_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_SECRET")
    )
    api = tweepy.API(auth)

    # Blog link (simulate, replace later with real hosting URL)
    blog_link = f"https://bharatbuzzai.github.io/{os.path.basename(blog_file)}"

    # Pick one image
    image_path = None
    if images:
        try:
            img_url = random.choice(images)
            img_data = requests.get(img_url, timeout=10).content
            image_path = "temp.jpg"
            with open(image_path, "wb") as f:
                f.write(img_data)
        except:
            image_path = None

    # Tweet
    tweet_text = f"{headline}\n\nRead more 👉 {blog_link}"
    if image_path:
        api.update_status_with_media(status=tweet_text, filename=image_path)
    else:
        api.update_status(status=tweet_text)

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    articles, images = scrape_articles()
    headline, summary = summarize_articles(articles)

    if headline and summary:
        blog_file = save_blog(headline, summary, articles)
        post_tweet(headline, blog_file, images)


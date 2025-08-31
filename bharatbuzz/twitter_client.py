import tweepy
import os

def create_twitter_client():
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_KEY_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    return client

def post_tweet(text, image_path=None):
    """
    Posts a tweet with optional image.
    """
    client = create_twitter_client()

    if image_path:
        # First, upload the media
        media = client.media_upload(filename=image_path)
        # Post tweet with image
        client.create_tweet(text=text, media_ids=[media.media_id])
    else:
        # Post text-only tweet
        client.create_tweet(text=text)


# twitter_client.py
import os
import tweepy

def get_api_v1():
    API_KEY = os.getenv("TWITTER_API_KEY")
    API_SECRET = os.getenv("TWITTER_API_SECRET")
    ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
        print("Twitter credentials missing. Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET")
        return None
    try:
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        api = tweepy.API(auth)
        return api
    except Exception as e:
        print("Error creating v1 API client:", e)
        return None

def post_tweet_with_image(text: str, image_path: str = None) -> bool:
    """
    Posts tweet with optional local image (path).
    Returns True on success.
    """
    api = get_api_v1()
    if not api:
        return False
    try:
        if image_path:
            media = api.media_upload(image_path)
            api.update_status(status=text[:280], media_ids=[media.media_id_string])
        else:
            api.update_status(status=text[:280])
        print("Tweet posted OK.")
        return True
    except Exception as e:
        print("Tweet failed:", e)
        return False

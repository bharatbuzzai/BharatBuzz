import os
import tweepy
from .config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET,
)
from .logger import log, log_error

def get_api_v1():
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        log("⚠️ Missing Twitter credentials (Secrets).")
        return None
    try:
        auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        api = tweepy.API(auth)
        # quick permission check
        me = api.verify_credentials()
        log(f"Twitter ready as @{getattr(me, 'screen_name', 'unknown')}")
        return api
    except Exception as e:
        log_error("Twitter init", e)
        return None

def post_tweet(text: str, media_path: str | None = None):
    api = get_api_v1()
    if not api:
        return False
    try:
        if media_path and os.path.exists(media_path):
            api.update_status_with_media(status=text[:280], filename=media_path)
        else:
            api.update_status(status=text[:280])
        log("✅ Tweet posted.")
        return True
    except Exception as e:
        log_error("Tweet", e)
        return False

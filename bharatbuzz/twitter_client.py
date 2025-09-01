import os
from tweepy import OAuth1UserHandler, API
from .logger import log
import os.path

def get_api():
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    if not all([api_key, api_secret, access_token, access_secret]):
        log("⚠️ Twitter credentials not fully present in environment.")
        return None
    try:
        auth = OAuth1UserHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_secret)
        api = API(auth, wait_on_rate_limit=True)
        # a harmless call could be api.verify_credentials() but avoid unless needed
        return api
    except Exception as e:
        log(f"Twitter API init error: {e}")
        return None

def post_tweet_with_media(status_text: str, media_path: str = None):
    api = get_api()
    if api is None:
        log("⚠️ Twitter API not available. Skipping tweet.")
        return False
    try:
        if media_path and os.path.exists(media_path):
            # upload and post
            media = api.media_upload(media_path)
            api.update_status(status=status_text[:280], media_ids=[media.media_id])
        else:
            api.update_status(status=status_text[:280])
        log("✅ Tweet posted.")
        return True
    except Exception as e:
        log(f"❌ ERROR while posting tweet: {e}")
        return False

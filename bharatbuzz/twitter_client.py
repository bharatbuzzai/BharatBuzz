import os
import sys
import tweepy

def post_tweet(message, image_path=None):
    try:
        # Load from environment (GitHub secrets)
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_secret = os.getenv("TWITTER_ACCESS_SECRET")

        # Authenticate (v2 client)
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )

        # If image is provided, upload via v1.1 API (media upload is not in v2 yet)
        if image_path:
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
            api = tweepy.API(auth)
            media = api.media_upload(image_path)
            response = client.create_tweet(text=message, media_ids=[media.media_id])
        else:
            response = client.create_tweet(text=message)

        print("✅ Tweet posted successfully!")
        print("Tweet URL: https://twitter.com/user/status/" + response.data['id'])

    except Exception as e:
        print("❌ ERROR while posting tweet:", str(e))
        sys.exit(1)

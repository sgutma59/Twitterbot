import tweepy
import requests
# allows us to use the operating system and load environment variables 
import os
from dotenv import load_dotenv
# allows the bot to choose one artwork at random
from random import randint

# pulling the keys and secrets from our .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# V1.1 API for media uploads
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# V2 client for creating tweets
client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

print('we loaded the auth variables')

def tweet_an_artwork(tweepy_v2_client, tweepy_v1_api, search_term):
    print(f'Fetching art for "{search_term}" from the MET...')

    # 1. Search for the given term, for objects on display and with images
    search_url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?hasImages=true&q={search_term}"
    r1 = requests.get(search_url)
    
    # Basic error handling
    if r1.status_code != 200:
        print(f"Error fetching object list: {r1.status_code}")
        return
    
    search_results = r1.json()
    if not search_results or not search_results.get('objectIDs'):
        print(f'No objects found for the search query: "{search_term}".')
        return

    object_ids = search_results['objectIDs']
    artwork_found = False
    parsed = None
    
    # 2. Loop to find a suitable artwork
    for i in range(1000): # Try up to 1000 times
        # 3. Select a random artwork from the list of results
        random_index = randint(0, len(object_ids) - 1)
        obj_id = object_ids[random_index]
        
        print(f"Attempt {i+1}/1000: Checking object {obj_id}...")
        
        r2 = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}")
        if r2.status_code != 200:
            continue # Skip if this object fails
            
        parsed = r2.json()

        # 4. Check that there is an image
        if parsed.get('primaryImage'):
            artwork_found = True
            break # Found one, exit the loop
    
    if not artwork_found:
        print(f"Couldn't find a suitable artwork for '{search_term}' after 1000 tries.")
        return

    # getting title, artist, and url
    title = parsed.get('title', 'Untitled')
    artist = parsed.get('artistDisplayName', 'Unknown Artist')
    url = parsed.get('objectURL', '')

    # getting image
    image_url = parsed['primaryImage']
    img = requests.get(image_url)
    img_content = img.content
    image_filename = 'image.jpg'
    with open(image_filename, 'wb') as handler:
        handler.write(img_content)

    try:
        # Upload image using v1.1 API
        media = tweepy_v1_api.media_upload(filename=image_filename)
        media_id = media.media_id_string

        # setting up the tweet text
        tweet_text = f"{title} by {artist}. See more: {url}"
        print('Tweeting artwork...')
        
        # Create tweet using v2 client
        tweepy_v2_client.create_tweet(text=tweet_text, media_ids=[media_id])
        print("Tweet sent successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 5. Clean up the downloaded image file
        if os.path.exists(image_filename):
            os.remove(image_filename)
 
# calling the function with the auth data and "robot" as the search term
tweet_an_artwork(client, api, "robot")
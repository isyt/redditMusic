#!pip install praw


# install packages bat file
# pip install praw
# pip install google-auth-oauthlib
# pip install oauth2client

# playlist creator bat file
# python ryplay.py
# pause

# config.json
# {"min_score":1000,
# "subreddits":["music","indieheads"],
# "timeunit":["day","week","month","year"]}

# redditapp.json
# {
#     "client_id":"replace text here with id",
#     "client_secret":"replace text here with secret",
#     "user_agent":"script by reddit user"
# }

print("Importing libraries...")
print("-"*50)

import google_auth_oauthlib.flow
import googleapiclient.discovery
import json
import os
import praw
import time
import datetime
from oauth2client import GOOGLE_REVOKE_URI, GOOGLE_TOKEN_URI, client


#files
reddit_app_file = "redditapp.json"
client_secrets_file = "client_secrets.json"
config_file="config.json"
refresh_token = "refresh_token.txt"

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl","https://www.googleapis.com/auth/youtube.readonly"]

#Configuration
config = json.load(open(config_file))
min_score=config['min_score']
subreddits=config['subreddits']
timeunit=config['timeunit']

print("Minimum score: ",min_score)
print("-"*50)
print("Subreddits:",*subreddits, sep='\n')
print("-"*50)
print("Sorted by time:",*timeunit, sep='\n')
print("-"*50)

reddit_info = json.load(open(reddit_app_file))

client_id = reddit_info['client_id']
client_secret = reddit_info['client_secret']
user_agent = reddit_info['user_agent']

google_info = json.load(open(client_secrets_file))

CLIENT_ID = google_info['installed']['client_id']
CLIENT_SECRET = google_info['installed']['client_secret']


def createRefreshToken():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    credentials = flow.run_console()
    with open('refresh_token.json', 'w', encoding='utf-8') as f:
        f.write(credentials.refresh_token)

# checks if there is refresh_token file, if not creates one
if not os.path.isfile("refresh_token.json"):
    createRefreshToken()
REFRESH_TOKEN=open("refresh_token.json").read()

print("Connecting to reddit...")
print("-"*50)

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
    check_for_async=False
)



print("Extracting youtube video IDs from reddit...")
print("-"*50)

video_ids=[]

for i in subreddits:
    for j in timeunit:
        print("Top submissions in "+i+" subreddit"+" this "+j)
        submissions=reddit.subreddit(i).top(j)
        for k in submissions:
            if 'youtu' in k.domain and k.score>min_score:
                main_url=k.url.split('&')[0]
                if 'watch' in main_url:
                    video_ids.append(main_url.split('=')[1])
                else:
                    video_ids.append(main_url.rsplit('/',1)[1])
        time.sleep(2)



print("Connecting to YouTube...")
print("-"*50)

credentials = client.OAuth2Credentials(
    access_token=None,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    refresh_token=REFRESH_TOKEN,
    token_expiry=None,
    token_uri=GOOGLE_TOKEN_URI,
    user_agent=None,
    revoke_uri=GOOGLE_REVOKE_URI)
api_service_name = "youtube"
api_version = "v3"
youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
try:
    request = youtube.channels().list(part="id",mine=True)
    response = request.execute()
except:
    print("Creating refresh token...")
    createRefreshToken()

def createPlaylist(title,description,privacyStatus):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": title,
            "description": description
          },
          "status": {
            "privacyStatus": privacyStatus
          }
        }
    )
    response = request.execute()
    return response['id']


def addVideos(playlist_id=None):
    if playlist_id:
        pid=playlist_id
    else:
        today_date=datetime.datetime.now().strftime("%B %d %Y")
        pid=createPlaylist(today_date+" Playlist",today_date+" Videos","public")
    existingIds=[]
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=pid,
        maxResults=50
    )
    response = request.execute()  
    totalResults=response['pageInfo']['totalResults']
    for i in range((totalResults//50)+1):
        if i>0:
            nextPageToken=response['nextPageToken']
        else:
            nextPageToken=""
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=pid,
            maxResults=50,
            pageToken=nextPageToken
        )
        response = request.execute()        
        existingIds+=[x['contentDetails']['videoId'] for x in response['items']]
    count=0
    for videoId in video_ids:
        if videoId not in existingIds:
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                  "kind": "youtube#playlistItem",
                  "snippet": {
                    "playlistId": pid,
                    "resourceId": {
                      "videoId": videoId,
                      "kind": "youtube#video"
                    }
                  }
                }
            )
            try:
                response = request.execute()
                count+=1
                if count==1:
                    print("Added ",count," video")
                else:
                    print("Added ",count," videos")
            except:
                print("Cannot find https://www.youtube.com/watch?v={}".format(videoId))
                pass
            time.sleep(1)


print("Adding videos to playlist...")
print("-"*50)

addVideos()

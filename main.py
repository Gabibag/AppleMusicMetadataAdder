# get Library.xml and convert to Library.csv with only track names
import os
import plistlib

import requests
from dotenv import load_dotenv

load_dotenv()
auth_url = 'https://accounts.spotify.com/api/token'

data = {
    'grant_type': 'client_credentials',
    'client_id': os.getenv("CLIENT_ID"),
    'client_secret': os.getenv("SPOTIFY_SECRET"),
}
if data['client_id'] is None or data['client_secret'] is None:
    print("Please add your client id and secret to the .env file. Use this format:\n"
          "CLIENT_ID=your_client_id\n"
          "SPOTIFY_SECRET=your_secret\n")
    print(
        "You can get your client id and secret here: https://developer.spotify.com/dashboard/applications. You must create an app to do so.")
    exit()
auth_response = requests.post(auth_url, data=data)

access_token = auth_response.json().get('access_token')

lib = '/Users/gabi/Documents/AMupdater/Library.xml'
# get the xml file and store it in a variable

print("Reading library.xml...")

with open(lib, 'rb') as fp:
    file = fp.read()
# get the root of the xml tree
try:
    plist = plistlib.loads(file)
    ogPlist = plist
except plistlib.InvalidFileException as e:
    print("Invalid file, check if it's been corrupted or if it exists.")
    exit()

# get the tracks
trackData = plist['Tracks']
trackNames = []
for trackId, track in trackData.items():
    # if the track has a bpm and a comment, skip it
    if 'BPM' in track and 'Comments' in track:
        continue
    # get the track genre, if it has Lofi in it, skip it

    try:
        trackNames.append(track['Name'] + '/ ' + track['Artist'])
    except:
        pass

scope = "user-library-read"

trackIds = []


def grabID():
    global results
    results = requests.get(
        'https://api.spotify.com/v1/search?q=track:"' + name
        + '"%20artist:"' + artist
        + '"&type=track&limit=1',
        headers={'Authorization': 'Bearer ' + access_token + ''}).json()
    trackIds.append(results['tracks']['items'][0]['id'])
    if len(trackIds) % 5 == 0:
        print(str(round(len(trackIds) / len(trackNames) * 100)) + "% done")


trackBPM = []
for track in trackNames:
    name = track.split('/')[0]
    artist = track.split('/')[1]
    artist = artist.split('&')
    artists = artist
    artist = artists[0]
    artist = artist.split(',')[0]
    try:
        grabID()
    except Exception as e:
        # check if name contains parentheses, if so, remove them and try again
        if '(' in name or '-' in name or name.isupper():
            name = name.split('(')[0]
            name = name.strip()
            name = name.replace('-', ' ')
            name = name.lower()
            try:
                grabID()
            except:
                pass
        # try again with a different artist
        try:
            if len(artists) > 1:
                for x in range(1, len(artists)):
                    artist = artists[x]
                    artist = artist.split(',')[0]
                    try:
                        grabID()
                        print("potential artist mismatch: " + name + " by " + artist + " != " +
                              results['tracks']['items'][0]['artists'][0]['name'])
                    except:
                        pass
        except:
            try:
                results = requests.get(
                    'https://api.spotify.com/v1/search?q=track:"' + name
                    + '"&type=track&limit=1',
                    headers={'Authorization': 'Bearer ' + access_token + ''}).json()
                trackIds.append(results['tracks']['items'][0]['id'] + "**")
                if not results['tracks']['items'][0]['artists'][0]['name'].strip() == artist.strip():
                    print("artist mismatch: " + name + " by " + artist + " != " +
                          results['tracks']['items'][0]['artists'][0]['name'])
            except Exception as e:

                print("not found: track " + name + " by " + artist)
                print(e)
                continue

    try:
        results = requests.get(
            'https://api.spotify.com/v1/audio-features/' + trackIds[-1].replace('**', ''),
            headers={'Authorization': 'Bearer ' + access_token + ''}).json()

        # add tempo and trackID to trackMeta
        if "**" in trackIds[-1]:
            name += "**"
        trackBPM.append(name + '/' + str(results['tempo']) + '/' + str(results['energy']))
        # print("bpm found for:  " + name + ", bpm: " + str(
        #     results['tempo']))
    except Exception as e:
        print("BPM not found: " + name)
        print(results)
        print(trackIds[-1])

# sort strackBPM by name
for x in range(0, len(trackBPM)):
    for y in range(0, len(trackBPM)):
        if trackBPM[x].split('/')[0].lower().replace("the ", "").replace("a ", "") < trackBPM[y].split('/')[0] \
                .lower().replace("the ", "").replace("a ", ""):
            temp = trackBPM[x]
            trackBPM[x] = trackBPM[y]
            trackBPM[y] = temp

# print out a formatted track list
for track in trackBPM:
    print(track.split('/')[0] + " -> " + str(round(float(track.split('/')[1]))) + "    energy: " + track.split('/')[
        2] + "\n")

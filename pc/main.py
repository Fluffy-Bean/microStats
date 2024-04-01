import time
import serial
import json
import spotipy
from spotipy import SpotifyOAuth
try:
    from config import (
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        SPOTIFY_REDIRECT_URI,
    )
except ImportError:
    print("config.py not found. Please create a config.py file with the following contents:")
    print("SPOTIFY_CLIENT_ID = \"your_spotify_client_id\"")
    print("SPOTIFY_CLIENT = \"your_spotify_client_secret\"")
    print("SPOTIFY_REDIRECT_URI = \"http://localhost:8888/callback\"")
    exit(1)


def get_tracks():
    auth_manager = SpotifyOAuth(
        scope='user-read-currently-playing',
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    data = sp.currently_playing()

    return (
        data['item']['name'],
        data['item']['album']['name'],
        data['item']['artists'][0]['name'],
        data['item']['duration_ms'],
        data['progress_ms']
    )


if __name__ == "__main__":
    print("connecting to serial device...")
    ser = serial.Serial('/dev/ttyACM0', 115200)
    print(ser.portstr)

    print("getting track info...")
    track_name, album_name, artist_name, length, progress = get_tracks()
    print(track_name, album_name, artist_name, length, progress)

    encoded = json.dumps({
        "track": {
            "name": track_name,
            "artist": artist_name,
            "album": album_name,
            "length": str(length) + "ms",
        },
    }).encode()
    print("Sending track info:", encoded)
    ser.write(encoded)

    # ToDO: Fix code to remove requirement of sleepy
    time.sleep(.1)

    encoded = json.dumps({
        "progress": str(progress) + "ms",
    }).encode()
    print("Sending progress info:", encoded)
    ser.write(encoded)

    time.sleep(.1)

    # ToDo: Implement a better solution for sending art
    encoded = json.dumps({
        "art": [0],  # Single black pixel
    }).encode()
    print("Sending art:", encoded)
    ser.write(encoded)

    # ToDo: Implement a better solution for reading error data
    while ser.in_waiting < 0:
        pass

    while ser.in_waiting > 0:
        print(ser.readline())

    ser.close()

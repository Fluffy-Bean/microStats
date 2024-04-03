import spotipy
from spotipy import SpotifyOAuth

import io
import requests
from PIL import Image

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


class Error(Exception):
    no_track = "No track currently playing"
    could_not_fetch_art = "Could not fetch album art"


class Spotify:
    def __init__(self):
        self.auth_manager = SpotifyOAuth(
            scope='user-read-currently-playing',
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_tracks(self) -> tuple:
        data = self.sp.currently_playing()

        if not data:
            Exception(Error.no_track)

        track_name = data['item']['name']
        album_name = data['item']['album']['name']
        artist_name = data['item']['artists'][0]['name']
        track_length = data['item']['duration_ms']
        listening_progress = data['progress_ms']
        cover_art = []
        try:
            cover_art = self._format_art(data['item']['album']['images'][2]['url'])
        except Error.could_not_fetch_art:
            cover_art = []

        return track_name, album_name, artist_name, track_length, listening_progress, cover_art

    @staticmethod
    def _format_art(url: str) -> list:
        req = requests.get(url, stream=True)

        if req.status_code != 200:
            print("Error: Could not fetch album art")
            raise Exception(Error.could_not_fetch_art)

        img = Image.open(io.BytesIO(req.content))
        img = img.resize((45, 45))
        img = img.convert('1')

        pixels = list(img.getdata())
        pixels = [1 if pixel == 255 else 0 for pixel in pixels]

        return pixels

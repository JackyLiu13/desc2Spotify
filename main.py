import os 
import re
from flask import Flask, session, url_for, redirect, request, render_template
from dotenv import load_dotenv
load_dotenv()

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)


client_id = os.getenv("CLIENT_ID") 
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
scope = "playlist-read-private playlist-modify-private playlist-modify-public"

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id, 
    client_secret=client_secret,
    redirect_uri=redirect_uri, 
    scope=scope, 
    cache_handler=cache_handler,
    show_dialog=True
)
sp = Spotify(auth_manager=sp_oauth)
def convert_song_names(description):
    pattern = r'\s*\d{2}:\d{2} '
    return [tuple(re.split(pattern, line.strip())[1].split(' - ')) for line in description.split('\n') if re.match(pattern, line)]

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))


@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists'))

@app.route('/get_playlists')
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    print("bomba")
    playlists = sp.current_user_playlists()
    playlist_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlists['items']]
    playlists_html = "<br>".join([f"<a href='{url}'>{name}</a>" for name, url in playlist_info])
    return f"<h1>Playlists</h1>{playlists_html}"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/create_playlist")
def create_playlist(descriptionSongs, playlist_name, username):
    #add songs to playlist    
    songs = convert_song_names(descriptionSongs)

    playlist = sp.user_playlist_create(username, playlist_name)
    for song, artist in songs:
        result = sp.search(q=f'track:{song} artist:{artist}', type='track', limit=1)
        # Extract the URI of the first track found
        if result['tracks']['items']:
            track_uri = result['tracks']['items'][0]['uri']
            sp.playlist_add_items(playlist['id'], [track_uri])
        else:
            print(f"Track {song} by {artist} not found")
    # return list of songs and artists
    output = "<a>Songs:<br></a>".join([f"{song} - {artist}" for song, artist in songs])
    return output

@app.route('/new_playlist', methods=['GET', 'POST'])
def new_playlist():
    if request.method == 'POST':
        descriptionSongs = request.form.get('descriptionSongs')
        playlist_name = request.form.get('playlist_name')
        username = request.form.get('username')  # Get the username from the form data
        return create_playlist(descriptionSongs, playlist_name, username)
    return render_template('new_playlist.html')

if __name__ == '__main__':
    app.run(debug=True)


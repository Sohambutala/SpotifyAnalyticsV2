"""
Prerequisites
    pip3 install spotipy Flask Flask-Session
    // from your [app settings](https://developer.spotify.com/dashboard/applications)
    export SPOTIPY_CLIENT_ID=client_id_here
    export SPOTIPY_CLIENT_SECRET=client_secret_here
            client_id="68047f44ff734cc79576042bbbf43358",
            client_secret="3ca39cfe870e4919876624ddd9a98ca0",
    export SPOTIPY_REDIRECT_URI='http://127.0.0.1:5000' // must contain a port
    // SPOTIPY_REDIRECT_URI must be added to your [app settings](https://developer.spotify.com/dashboard/applications)
    OPTIONAL
    // in development environment for debug output
    export FLASK_ENV=development
    // so that you can invoke the app outside of the file's directory include
    export FLASK_APP=/path/to/spotipy/examples/app.py
    // on Windows, use `SET` instead of `export`
Run app.py
    python3 app.py OR python3 -m flask run
    NOTE: If receiving "port already in use" error, try other ports: 5000, 8090, 8888, etc...
        (will need to be updated in your Spotify app and SPOTIPY_REDIRECT_URI variable)
"""

import os

from flask import Flask, session, request, redirect, render_template
from flask_session import Session
import spotipy
import pyrebase
import pandas as pd
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

app.secret_key = 'dsajnfirunvaipnbdfr'
app.config['SESSION_COOKIE_NAME'] = 'My_own_cookie'

#firebase config
config = {
    "apiKey": "AIzaSyDrNPUIT3D84YD-XXUWtDi1M9K9i62R-O8",
    "authDomain": "spotifydataanalysis.firebaseapp.com",
    "projectId": "spotifydataanalysis",
    "storageBucket": "spotifydataanalysis.appspot.com",
    "messagingSenderId": "888432911140",
    "databaseURL": "gs://spotifydataanalysis.appspot.com",
    "serviceAccount":"spotifydataanalysis-firebase-adminsdk-52bcp-8ed0394572.json"
    
}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()

@app.route('/')
def initialize():
    session['ver']=0
    return render_template('Home.html')


@app.route('/oauth', methods=['GET','POST'])
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    if request.method == 'POST':
        print('inside index')
        user_email = request.form['email']
        df=pd.read_csv("data/spotify_emails_responses.csv")
        #Assuming that this has email, names, split(number, denoting the split of the email)
        print(user_email)
        ver=int(df[df['email']==user_email]['split'])
        session["ver"]=ver
        
    ver=session["ver"]
    #redirect_uri="http://spotifydataanalytics.azurewebsites.net"
    if ver==1:
        auth_manager = spotipy.oauth2.SpotifyOAuth(scope="user-library-read,user-read-recently-played,user-read-playback-state,user-follow-read,user-read-currently-playing,user-top-read", 
                                                cache_handler=cache_handler,
                                            show_dialog=True, client_id="68047f44ff734cc79576042bbbf43358",
                                            client_secret="3ca39cfe870e4919876624ddd9a98ca0",
                                            redirect_uri="http://spotifydataanalytics.azurewebsites.net/oauth"
                                            )
    else:
        if session['ver']==0:
            print('error')
        auth_manager = spotipy.oauth2.SpotifyOAuth(scope="user-library-read,user-read-recently-played,user-read-playback-state,user-follow-read,user-read-currently-playing,user-top-read", 
                                                cache_handler=cache_handler,
                                            show_dialog=True, client_id="68047f44ff734cc79576042bbbf43358",
                                            client_secret="3ca39cfe870e4919876624ddd9a98ca0",
                                            redirect_uri="http://spotifydataanalytics.azurewebsites.net/oauth")

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        print('got the code')
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/oauth')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return redirect(auth_url)
        #render_template('Home.html')


    # Step 3. Signed in, display data
    sp = spotipy.Spotify(auth_manager=auth_manager)
    #user_email = request.form['email']

    #using the api to fetch the data
    current_user=sp.current_user()
    current_user_recently_played=sp.current_user_recently_played(limit=50)
    current_playback=sp.current_playback()
    current_user_followed_artists=sp.current_user_followed_artists(limit=50, after=None)
    current_user_playing_track=sp.current_user_playing_track()
    current_user_playlists=sp.current_user_playlists(limit=50, offset=0)
    
    print(current_user)
    results = {}
    iter = 0
    while True:
        offset = iter * 50
        iter += 1
        curGroup = sp.current_user_saved_tracks(limit=50, offset=offset)['items']
        results[iter]=curGroup
        if (len(curGroup) < 50):
            break
            #create the json object
    final={
        'current_user':current_user,
        'current_user_recently_played':current_user_recently_played,
        'current_playback':current_playback,
        'current_user_followed_artists':current_user_followed_artists,
        'current_user_playing_track':current_user_playing_track,
        'current_user_playlists':current_user_playlists,
        'current_user_saved_tracks':results 
    
    }

    name=final['current_user']['uri'].split(':')[2]

    #print(final)
    #storing data in json
    with open('data/'+name+'.json', 'w') as f:
        json.dump(final, f)
    storage.child("data/"+name+".json").put(name+'.json')
    
    
    return render_template('Exit.html')




    # return f'<h2>Hi {spotify.me()["display_name"]}, ' \
    #        f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
    #        f'<a href="/playlists">my playlists</a> | ' \
    #        f'<a href="/currently_playing">currently playing</a> | ' \
    #     f'<a href="/current_user">me</a>' \



@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
# if __name__ == '__main__':
#     app.run(threaded=True, port=int(os.environ.get("PORT",
#                                                    os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))

from flask import Flask, redirect, url_for, render_template, request, session, flash
import datetime
from urllib.parse import urlencode
import base64
import requests
import pdb
import os


app = Flask(__name__)

client_id = os.environ.get('SPOTIFY_CLIENT_ID')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')


class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url="https://accounts.spotify.com/api/token"

    @app.route("/")
    def home():
    	return render_template("index.html")

    @app.route("/get_artist", methods=['GET','POST'])
    def get_artist():
        get_artist = request.form['artist']

        return spotify.get_related_artists(get_artist)

        #pdb.set_trace()
        #return render_template("get_artist.html", data=data)

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        """
        return as base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }

    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        }

    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if  r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
            # return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in']       # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers

    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()

    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')

    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')

    def search(self, query, search_type='artist', limit=1):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        data = urlencode({"q": query, "type": search_type.lower(), "limit": limit})
        lookup_url = f"{endpoint}?{data}"
        print(lookup_url)
        r = requests.get(lookup_url, headers=headers)
        d = r.json()
        if r.status_code not in range(200, 299):
            return {}
        return d['artists']['items'][0]['id']

    def get_related_artists(self, artist):
        _id = self.search(artist)
        headers = self.get_resource_header()
        endpoint = f"https://api.spotify.com/v1/artists/{_id}/related-artists"
        r = requests.get(endpoint, headers=headers)
        d = r.json()

        result_dict = dict((i['name'], i['images'][0]['url']) for i in d['artists'])
        print(result_dict)
        #for artist in d['artists']:
            #print(artist['name'], '----', artist['images'][0]['url'])

        #pdb.set_trace()
        #return render_template("index.html", data=result_dict)
        #return redirect(url_for('get_artist', data=result_dict))
        return render_template("get_artist.html", data=result_dict)


spotify = SpotifyAPI(client_id, client_secret)


if __name__ == "__main__":
	app.run(debug=True)

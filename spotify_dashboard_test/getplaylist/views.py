from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import requests
import random
from http import HTTPStatus
from django.template import loader
import base64
from django.conf import settings as django_settings

'''
http://127.0.0.1:8000/getplaylist/login
http://127.0.0.1:8000/getplaylist/get
'''

SPOTIFY_ACCESS_TOKEN=''
SPOTIFY_REFRESH_TOKEN=''
SPOTIFY_TOKEN_EXPIRATION=''
SPOTIFY_TOKEN_SCOPES=''
SPOTIFY_ENDPOINT='https://api.spotify.com/v1'


def html_error(error_title, error_content, error_code):
    template = loader.get_template('error.html')
    context = {
        'error_title' : error_title, 
        'error_content' : error_content
    }
    return HttpResponse(template.render(context), status=error_code)

def html_code_dump(title, content, status_code=200):
    template = loader.get_template('dump.html')
    context = {
        'title' : title, 
        'content' : content
    }
    return HttpResponse(template.render(context), status=status_code)



def start_login(request):
    """ URL: 
    /getplaylist/login
    http://127.0.0.1:8000/getplaylist/login
    
    """
    scopes = [ 
        'playlist-read-private', 
        'playlist-read-collaborative', 
    ]
    client_id = django_settings.SPOTIFY_CLIENT_ID
    redirect_uri = 'http://localhost:8000/getplaylist/login_callback'

    res = requests.get(
        url = 'https://accounts.spotify.com/authorize',
        params = {
            'client_id' : client_id,
            'response_type' : 'code',
            'redirect_uri' : redirect_uri,
            'state' : random.randint(1000, 9999),
            'scope' : ' '.join(scopes),
            'show_dialog' : 'true',
        },
        allow_redirects = True, 
    )

    if res.status_code != HTTPStatus.OK:
        return html_error(f"ERROR: server returned {res.status_code}", res.content.decode('utf-8'), res.status_code)
    elif len(res.history) == 0:
        return html_error(f"ERROR: server returned {res.status_code}", "empty redirect list.\n" + res.content.decode('utf-8'), res.status_code)
    elif 'Location' not in res.history[0].headers.keys():
        return html_error(f"ERROR: cannot find redirect address.", res.history[0].content.decode('utf-8'), res.status_code)
    return HttpResponseRedirect(res.history[0].headers['Location'])



def end_login(request):
    """ URL:
    /getplaylist/login_callback

    """
    global SPOTIFY_ACCESS_TOKEN, SPOTIFY_REFRESH_TOKEN, SPOTIFY_TOKEN_EXPIRATION, SPOTIFY_TOKEN_SCOPES
    
    client_id = django_settings.SPOTIFY_CLIENT_ID
    client_secret = django_settings.SPOTIFY_CLIENT_SECRET
    client_b64_key = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    code = request.GET.get('code')
    redirect_uri = 'http://localhost:8000/getplaylist/login_callback'

    res = requests.post(
        url = 'https://accounts.spotify.com/api/token',
        headers = {
            'Authorization' : f'Basic {client_b64_key}',
            'Content-Type' : 'application/x-www-form-urlencoded', 
        },
        data = "&".join([
            'grant_type=authorization_code',
            f'code={code}',
            f'redirect_uri={redirect_uri}',
        ]),
    )

    if res.status_code != HTTPStatus.OK:
        return html_error(f"ERROR: server returned {res.status_code}", res.content.decode('utf-8'), res.status_code)
    
    SPOTIFY_ACCESS_TOKEN=res.json()['access_token']
    SPOTIFY_REFRESH_TOKEN=res.json()['refresh_token']
    SPOTIFY_TOKEN_EXPIRATION=res.json()['expires_in']
    SPOTIFY_TOKEN_SCOPES=res.json()['scope']
    # return html_code_dump("OK! Request Success.", json.dumps(res.json(), indent=4), status_code=200) # TODO: redirect verso l'app che ha richiesto l'accesso
    return HttpResponseRedirect('http://localhost:8000/getplaylist/get')



def get_playlists(request):
    global SPOTIFY_ACCESS_TOKEN, SPOTIFY_REFRESH_TOKEN, SPOTIFY_TOKEN_EXPIRATION, SPOTIFY_TOKEN_SCOPES
    res = requests.get(
        url = f'{SPOTIFY_ENDPOINT}/me/playlists',
        headers = {
            'Authorization' : f'Bearer {SPOTIFY_ACCESS_TOKEN}',
        }
    )

    if res.status_code != HTTPStatus.OK:
        return html_error(f"ERROR: server returned {res.status_code}", res.content.decode('utf-8'), res.status_code)

    res_json = res.json()
    total = res_json['total']
    next = res_json['next']
    items_list = list()
    for item in res_json['items']:
        items_list.append({
            'id' : item['id'],
            'name' : item['name'],
            'url' : item['external_urls']['spotify'],
        })
    
    return render(request, "getplaylist.html", {
        'page_details' : f'Total: {total} | Next: <a href="{next}">{next}</a>',
        'items_list' : items_list,
    })
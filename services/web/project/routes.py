from flask import Blueprint, request, redirect, session, render_template, url_for, jsonify
import os
from dotenv import load_dotenv
from .extensions import oauth
from .osint import *
import ipinfo
import requests

load_dotenv('~/.env')  # load environment variables
views = Blueprint('views', __name__)


@views.route('/')
def index():
    return render_template('index.html')


@views.route('/login_successful')
def login_successful():
    user_info = session.get('user_info')
    service = session.get('service')

    if user_info and service:
        user_id = user_info['id']
        existing_data = DeepdiveResult.query.filter_by(user_id=user_id).first()

        if existing_data is None:
            get_deepdive.delay(user_id)

        user_ip = get_user_ip()
        location_info = None

        if user_ip is not None:
            user_info['user_ip'] = user_ip

            access_token = os.getenv('IPINFO')
            handler = ipinfo.getHandler(access_token)
            details = handler.getDetails(user_ip)

            location_info = {
                'city': details.city,
                'country': details.country_name,
                'coordinates': details.loc
            }

        user_info['ip_details'] = location_info
        session['user_info'] = user_info

        user = User.query.filter_by(platform_id=user_id).first()
        search_query = user.firstname + " " + user.lastname
        query = f'q=#gsc.tab=1&gsc.sort=&gsc.q={search_query}&gsc.tab=1&gsc.page=1'
        return redirect(url_for('views.user_login', _anchor=query))

    return redirect(url_for('views.index'))


@views.route('/user_login')
def user_login():
    service = session.get('service')
    user_info = session.get('user_info')
    print("SERVICE: " + service)
    if service == 'facebook':
        return render_template('facebook_index.html', user_info=user_info)
    return render_template(f'{service}_index.html', user_info=user_info)


def get_user_ip():
    if request.headers.getlist("X-Forwarded-For"):
        user_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        user_ip = request.remote_addr
    return user_ip


@views.route('/get_all_links')
def get_all_links():
    user_info = session.get('user_info')
    user_id = user_info['id']

    deepdive_result = DeepdiveResult.query.filter_by(user_id=user_id).first()

    if deepdive_result:
        all_links = {
            'instagram': json.loads(deepdive_result.instagram_links) if deepdive_result.instagram_links else [],
            'reddit': json.loads(deepdive_result.reddit_links) if deepdive_result.reddit_links else [],
            'twitter': json.loads(deepdive_result.twitter_links) if deepdive_result.twitter_links else [],
            'linkedin': json.loads(deepdive_result.linkedin_links) if deepdive_result.linkedin_links else [],
            'other_links': json.loads(deepdive_result.other_links) if deepdive_result.other_links else [],
            'possible_accounts': json.loads(deepdive_result.possible_accounts) if deepdive_result.other_links else [],
            'facebook': json.loads(deepdive_result.facebook_links) if deepdive_result.facebook_links else []
        }
        return jsonify(all_links)
    else:
        return jsonify({'message': 'Data not ready'})


@views.route('/awareness')
def awareness():
    return render_template('awareness.html')


@views.route('/privacy')
def privacy():
    return render_template('privacy.html')


@views.route('/linkedin/login')
def linkedin_login():
    # Redirect the user to LinkedIn's authorization page
    print(os.getenv('REDIRECT_URI'))
    url = 'https://www.linkedin.com/oauth/v2/authorization'
    params = {
        'response_type': 'code',
        'client_id': os.getenv('LINKEDIN_CLIENT_ID'),
        'redirect_uri': os.getenv('REDIRECT_URI'),
        'state': 'foobar',
        'scope': 'r_basicprofile r_emailaddress',
    }
    # GET request for the URL with the concetinated params
    return redirect(requests.Request('GET', url, params=params).prepare().url)


@views.route('/linkedin/callback')
def linkedin_callback():
    # LinkedIn has redirected the user here with a code
    code = request.args.get('code')

    # Exchange this code for an access token
    url = 'https://www.linkedin.com/oauth/v2/accessToken'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': os.getenv('LINKEDIN_CLIENT_ID'),
        'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET'),
        'redirect_uri': os.getenv('REDIRECT_URI'),
    }
    response = requests.post(url, data=data)
    response.raise_for_status()  # Ensure we got a successful response

    # We have an access token
    access_token = response.json()['access_token']

    # Store the access token in the user's session
    session['access_token'] = access_token

    headers = {'Authorization': 'Bearer ' + access_token}
    user_info = {}
    response = requests.get('https://api.linkedin.com/v2/me', headers=headers)
    if response.status_code == 200:
        # Access token is valid
        user_info = response.json()
        # Process the user's LinkedIn profile data as needed
        print("LinkedIn Profile Data:", user_info)
    else:
        # Access token is invalid or expired
        print("Invalid Access Token")

    response = requests.get(
        'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
        headers=headers
    )

    if response.status_code == 200:
        # Successful email request
        email_data = response.json()
        print("LinkedIn Email Data:", email_data)

        # Extract the user's email address and add it to user_info
        if email_data.get('elements'):
            email_handle = email_data['elements'][0]['handle~']
            user_info['emailAddress'] = email_handle.get('emailAddress')
    else:
        # Email request failed
        print("Failed to fetch email")

    session['user_info'] = user_info
    session['service'] = 'linkedin'
    user = User.query.filter_by(platform_id=user_info['id'], type='linkedin').first()
    if not user:
        user = LinkedinUser(firstname=user_info['localizedFirstName'], lastname=user_info['localizedLastName'],
                            email=user_info['emailAddress'], platform_id=user_info['id'],
                            headline=user_info['localizedHeadline'])
        db.session.add(user)
        db.session.commit()

    return redirect(url_for('views.login_successful'))


@views.route('/google/')
def google():
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_KEY')
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'  # add scopes ?
        }
    )

    # Redirect to google_auth function
    redirect_uri = url_for('views.google_auth', _external=True, _scheme='https')
    print(redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri)


@views.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    response = oauth.google.get('https://www.googleapis.com/oauth2/v1/userinfo')
    user_info = response.json()
    print(" Google User ", user_info)
    session['user_info'] = user_info
    session['service'] = 'google'
    user = User.query.filter_by(platform_id=user_info['id'], type='google').first()
    if not user:
        user = GoogleUser(firstname=user_info['given_name'], lastname=user_info['family_name'],
                          email=user_info['email'], platform_id=user_info['id'])
        db.session.add(user)
        db.session.commit()

    print("Session after setting service:", session)
    return redirect(url_for('views.login_successful'))


@views.route('/process_facebook_data', methods=['POST'])
def process_facebook_data():
    user_info = request.json

    session['user_info'] = user_info
    session['service'] = 'facebook'
    print(user_info)

    user = User.query.filter_by(platform_id=user_info['id'], type='facebook').first()
    if not user:
        user = FacebookUser(firstname=user_info['first_name'], lastname=user_info['last_name'],
                            email=user_info['email'], platform_id=user_info['id'])
        db.session.add(user)
        db.session.commit()

    return jsonify({'status': 'success'})


@views.route('/imprint')
def imprint():
    return render_template('imprint.html')


@views.route('/logout')
def logout():
    user_info = session.get('user_info', None)
    if user_info:
        user_id = user_info.get('id')
        user = User.query.filter_by(platform_id=user_id).first()
        if user:
            DeepdiveResult.query.filter_by(user_id=user_id).delete()
            if isinstance(user, GoogleUser) or isinstance(user, LinkedinUser) or isinstance(user, FacebookUser):
                db.session.delete(user)

        db.session.commit()

    session.clear()
    return redirect(url_for('views.index'))  # Redirect to the home page

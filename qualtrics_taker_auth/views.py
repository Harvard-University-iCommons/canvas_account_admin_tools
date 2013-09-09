from django.shortcuts import render, redirect
from time import gmtime, strftime, time
import hmac
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
import bitly_api
import os
from django.http import HttpRequest

# Create your views here.


def index(request):

    if request.GET.get('qtarget') is not None:
        """ 
        if the request contains a target, create the token and redirect the user to qualtrics
        """

        user = request.user
        target_url = base64.b64decode(request.GET.get('qtarget').strip())

        ssotoken = get_qualtrics_token(user)

        target_url = base64.b64decode(request.GET.get('qtarget')) + '&ssotoken=%s' % ssotoken
        return redirect(target_url)

    elif request.GET.get('qtarget_url') is not None:
        """
        else if the request contains a target_url, give them a page with a distributable target_url
        """
        qtarget_url = request.GET.get('qtarget_url').strip()

        if not qtarget_url.startswith('https://harvard.qualtrics.com/'):
            message = "Sorry, you can only use this tool to link to Harvard Qualtrics surveys."
            return render(request, 'qualtrics_taker_auth/index.html', {'message': message})
            
        target = base64.b64encode(qtarget_url)

        dist_url = HttpRequest.build_absolute_uri(request, '%s?qtarget=%s' % (request.path, target))

        short_url = get_bitly_url(dist_url)

#        from pudb import set_trace; set_trace()

        return render(request, 'qualtrics_taker_auth/index.html', {'qtarget_url': qtarget_url, 'dist_url': dist_url, 'short_url': short_url})

    else: 
        """
        if the request doesn't contain a target and the request doesn't contain a target_url, then give the user a form to enter one
        """

        return render(request, 'qualtrics_taker_auth/index.html')


def get_qualtrics_token(user):
    # generate the token
    token_timestamp = strftime('%Y-%m-%dT%H:%M:%S', gmtime())
    token_expiration = strftime('%Y-%m-%dT%H:%M:%S', gmtime(time() + (60*5)))

    """
    qualtrics token fields: id, timestamp, expiration, mac, firstname, lastname, email
    """

    userid_hash = hashlib.sha256(user.username).hexdigest()
    if user.role_type_cd == 'XIDHOLDER':
        id_type = 'XID'
    elif user.role_type_cd == 'POSTHARVARD':
        id_type = 'POST'
    else:
        id_type = 'HUID'

    token_string = 'id=%s&timestamp=%s&expiration=%s&firstname=%s&lastname=%s&email=%s&id_type=%s' % (userid_hash, token_timestamp, token_expiration, user.first_name, user.last_name, user.email, id_type)

    if 'QUALTRICS_API_KEY' not in os.environ:
        raise ValueError("Environment variable '{}' required".format('QUALTRICS_API_KEY'))
    qualtrics_api_key = os.getenv('QUALTRICS_API_KEY')

    mac = base64.b64encode(hmac.new(qualtrics_api_key, token_string, hashlib.md5).digest())

    token_with_mac = token_string + '&mac=%s' % mac
    iv = Random.new().read(AES.block_size)

    enc = AES.new(qualtrics_api_key, AES.MODE_ECB, iv)
    encrypted_token = base64.b64encode(enc.encrypt(PKCS5Padding(token_with_mac)))

    return encrypted_token


def get_bitly_url(dist_url):
    BITLY_ACCESS_TOKEN = "BITLY_ACCESS_TOKEN"

    if BITLY_ACCESS_TOKEN not in os.environ:
        raise ValueError("Environment variable '{}' required".format(BITLY_ACCESS_TOKEN))
    access_token = os.getenv(BITLY_ACCESS_TOKEN)
    bitly = bitly_api.Connection(access_token=access_token)

    bitly_data = bitly.shorten(dist_url, preferred_domain='hvrd.me')
    short_url = bitly_data['url']
    return short_url


def PKCS5Padding(string):
    byteNum = len(string)
    packingLength = 16 - byteNum % 16
    if packingLength == 16:
        return string
    else:
        appendage = chr(packingLength) * packingLength
        return string + appendage



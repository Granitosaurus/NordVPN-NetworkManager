from typing import Tuple, Union

import requests
import json
from operator import itemgetter
import hashlib

API_ADDR = 'https://api.nordvpn.com'
OVPN_ADDR = 'https://downloads.nordcdn.com/configs/archives/servers/ovpn.zip'
TIMEOUT = 5

# Mapping of NordVPN category names to their short internal names
VPN_CATEGORIES = {
    'Standard VPN servers': 'normal',
    'P2P': 'p2p',
    'Double VPN': 'double',
    'Dedicated IP servers': 'dedicated',
    'Onion over VPN': 'onion',
    'Anti DDoS': 'ddos',
}


def get_server_list(sort_by_load=False, sort_by_country=False):
    try:
        resp = requests.get(API_ADDR + '/server', timeout=TIMEOUT)
        if resp.status_code == requests.codes.ok:
            server_list = resp.json()

            if sort_by_load:
                return sorted(server_list, key=itemgetter('load'))
            elif sort_by_country:
                return sorted(server_list, key=itemgetter('country'))
            else:
                return server_list
        else:
            return None
    except Exception as ex:
        return None


def get_nameservers():
    return ['162.242.211.137', '78.46.223.24']

    # Apparently this is not the standard DNS endpoint, but something to do with 'smart-play' and no longer provides valid nameservers
    # so for now we will just return a static list...
    """
    try:
        resp = requests.get(API_ADDR + '/dns/smart', headers=HEADERS, timeout=TIMEOUT)
        return resp.json()
    except Exception as ex:
        return None
    """


def get_ovpn_configs(etag=None) -> Union[Tuple[bytes, str], None]:
    """
    Retrieve openvpn configs from nordvpn servers
    :return: bytes content, etag
    """
    head = requests.head(OVPN_ADDR, timeout=TIMEOUT, allow_redirects=True)
    header_etag = head.headers['etag']
    if etag == header_etag:
        return None
    resp = requests.get(OVPN_ADDR, timeout=TIMEOUT)
    if resp.status_code == requests.codes.ok:
        return resp.content, header_etag


def get_user_token(email):
    """
    Returns {"token": "some_token", "key": "some_key", "salt": "some_salt"}
    """

    try:
        resp = requests.get(API_ADDR + '/token/token/' + email, timeout=TIMEOUT)
        if resp.status_code == requests.codes.ok:
            return json.loads(resp.text)
        else:
            return None
    except Exception as ex:
        return None


def validate_user_token(token_json, password):
    token = token_json['token']
    salt = token_json['salt']
    key = token_json['key']

    password_hash = hashlib.sha512(salt.encode() + password.encode())
    final_hash = hashlib.sha512(password_hash.hexdigest().encode() + key.encode())

    try:
        resp = requests.get(API_ADDR + '/token/verify/' + token + '/' + final_hash.hexdigest(), timeout=TIMEOUT)
        if resp.status_code == requests.codes.ok:
            return True
        else:
            return False
    except Exception as ex:
        return None


def verify_user_credentials(email, password):
    token_json = get_user_token(email)
    return validate_user_token(token_json, password)

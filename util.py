# -*- coding=utf-8 -*-
import hashlib
import json
import socket
import requests

_dnscache = {}

def parse_json(s):
    begin = s.find('{')
    end = s.rfind('}') + 1
    return json.loads(s[begin:end])


def getconfigMd5():
    with open('configDemo.ini', 'r', encoding='utf-8') as f:
        configText = f.read()
        return hashlib.md5(configText.encode('utf-8')).hexdigest()

def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


def _setDNSCache():
    """
    Makes a cached version of socket._getaddrinfo to avoid subsequent DNS requests.
    """

    def _getaddrinfo(*args, **kwargs):
        global _dnscache
        if args in _dnscache:
            # print(str(args) + " in cache")
            return _dnscache[args]

        else:
            # print(str(args) + " not in cache")
            _dnscache[args] = socket._getaddrinfo(*args, **kwargs)
            return _dnscache[args]

    if not hasattr(socket, '_getaddrinfo'):
        socket._getaddrinfo = socket.getaddrinfo
        socket.getaddrinfo = _getaddrinfo

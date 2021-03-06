"""This module contains a basic (skeletal) implementation of the webfinger
protocol. Webfinger is used to discover information about actors in
ActivityPub using regular HTTP methods (i.e. no RESTful api here).

There's some useful discussion here about the intersection of
webfinger and ActivityPub:
https://github.com/w3c/activitypub/issues/194

TODO: tests for this using our own webfinger endpoints
"""
import re
from urllib.parse import urlparse
from typing import Tuple
from aiohttp import ClientSession
import ujson as json

from lamia.version import VERSION

PORT_RE = re.compile(r'(\:\d+)')


def normalize(identifier: str, allow_port: bool = False) -> Tuple[str, str]:
    """Given an id, returns a tuple of (resource, address,) to contact

    A rough, heuristic approximation of:
    https://openid.net/specs/openid-connect-discovery-1_0.html#NormalizationSteps

    Note: We assume that we will never call for details over http."""

    _identifier = identifier

    # Drop the acct: portion
    # examples - acct:lamia@lamia.social OR acct:lamia.social/@lamia
    if _identifier.startswith('acct:'):
        _identifier = _identifier[5:]

    # # Drop the port portion of an identifier
    if not allow_port:
        if ':' in _identifier.replace('://', ''):
            _identifier = PORT_RE.sub('', _identifier)

    # If the id is an address, then we're done here, parse and return
    # examples - http://lamia.social/users/lamia OR http://lamia.social/lamia
    if _identifier.startswith('http'):
        parsed_id = urlparse(_identifier)
        return (
            _identifier.replace('https://', '').replace('http://', ''),
            f'https://{parsed_id.netloc}',
        )

    # If the id is an email address-style thing, split it and return
    # examples - lamia@lamia.social
    if '@' in _identifier and not '/@' in _identifier:
        split_id = _identifier.split('@')
        return (
            _identifier,
            f'https://{split_id[1]}',
        )

    # For everything else, assume it's a url sans http and return
    parsed_id = urlparse(f'https://{_identifier}')
    return (
        _identifier,
        f'https://{parsed_id.netloc}',
    )


async def finger(identifier: str) -> dict:
    """When provided with an id, returns the webfinger query for it

    https://tools.ietf.org/html/rfc7033"""
    headers = {
        # We aren't going to be accepting anything other than json
        'Accept': 'q=2, application/jrd+json; q=1, application/json',
        # Gotta be a good neighbor
        'User-Agent': f'Lamia/{VERSION}',
    }

    uid, url = normalize(identifier)
    params = {'resource': uid}
    url = url + "/.well-known/webfinger"

    # ref: https://docs.aiohttp.org/en/stable/client_reference.html
    async with ClientSession() as async_session:
        async with async_session.get(
                url, headers=headers, params=params) as response:
            return await json.loads(response.read())

"""
Simple wrappers around request methods.
"""

import logging
import sys

import requests

import git_pw
from git_pw import config

if 0:  # noqa
    from typing import Dict  # noqa

CONF = config.CONF
LOG = logging.getLogger(__name__)


class HTTPTokenAuth(requests.auth.AuthBase):
    """Attaches HTTP Token Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self._token_auth_str(self.token)
        return r

    @staticmethod
    def _token_auth_str(token):  # type: (str) -> str
        """Return a Token auth string."""
        return 'Token {}'.format(token.strip())


def _get_auth():  # type: () -> requests.auth.AuthBase
    if CONF.token:
        return HTTPTokenAuth(CONF.token)
    elif CONF.username and CONF.password:
        return requests.auth.HTTPBasicAuth(CONF.username, CONF.password)
    else:
        LOG.error('Authentication information missing')
        LOG.error('You must configure authentication via git-config or via '
                  '--token or --username, --password')
        sys.exit(1)


def _get_headers():  # type: () -> Dict[str, str]
    return {
        'User-Agent': 'git-pw ({})'.format(git_pw.__version__),
    }


def _get_server():  # type: () -> str
    if CONF.server:
        return CONF.server.rstrip('/')
    else:
        LOG.error('Server information missing')
        LOG.error('You must provide server information via git-config or via '
                  '--server')
        sys.exit(1)


def get(url, params=None):  # type: (str, dict) -> requests.Response
    """Make GET request and handle errors."""
    LOG.debug('GET %s', url)

    try:
        rsp = requests.get(url, auth=_get_auth(), headers=_get_headers(),
                           params=params)
        rsp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        if exc.response is not None and exc.response.content:
            # we make the assumption that all resposes will be JSON encoded
            LOG.error(exc.response.json()['detail'])
        else:
            LOG.error('Failed to fetch resource. Is your configuration '
                      'correct?')
            LOG.error("Use the '--debug' flag for more information")

        if CONF.debug:
            raise
        else:
            sys.exit(1)

    LOG.debug('Got response')

    return rsp


def put(url, data):  # type: (str, dict) -> requests.Response
    """Make PUT request and handle errors."""
    LOG.debug('PUT %s, data=%r', url, data)

    try:
        rsp = requests.patch(url, auth=_get_auth(), headers=_get_headers(),
                             data=data)
        rsp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        if exc.response is not None and exc.response.content:
            LOG.error(exc.response.json()['detail'])
        else:
            LOG.error('Failed to update resource. Is your configuration '
                      'correct?')
            LOG.error("Use the '--debug' flag for more information")

        if CONF.debug:
            raise
        else:
            sys.exit(1)

    LOG.debug('Got response')

    return rsp


def index(resource_type, params=None):  # type: (str, dict) -> dict
    """List API resources.

    GET /{resource}/

    All resources are JSON bodies, thus we can access them in a similar
    fashion.

    Arguments:
        resource_type (str): The resource endpoint name.
        params (dict/list): Additional parameters, filters.

    Returns:
        A list of dictionaries, representing the summary view of each resource.
    """
    # NOTE(stephenfin): All resources must have a trailing '/'
    url = '/'.join([_get_server(), 'api', resource_type, ''])

    return get(url, params).json()


def detail(resource_type, resource_id, params=None):
    # type: (str, int, dict) -> dict
    """Retrieve a specific API resource.

    GET /{resource}/{resourceID}/

    Arguments:
        resource_type (str): The resource endpoint name.
        resource_id (int/str): The ID for the specific resource.
        params (dict/list): Additional parameters.

    Returns:
        A dictionary representing the detailed view of a given resource.
    """
    # NOTE(stephenfin): All resources must have a trailing '/'
    url = '/'.join([_get_server(), 'api', resource_type,
                    str(resource_id), ''])

    return get(url, params).json()


def update(resource_type, resource_id, data):
    # type: (str, int, dict) -> dict
    """Update a specific API resource.

    PUT /{resource}/{resourceID}/

    Arguments:
        resource_type (str): The resource endpoint name.
        resource_id (int/str): The ID for the specific resource.
        params (dict/list): Fields to update.

    Returns:
        A dictionary representing the detailed view of a given resource.
    """
    url = '/'.join([CONF.server.rstrip('/'), 'api', '1.0', resource_type,
                    str(resource_id), ''])

    return put(url, data).json()

"""
Simple wrappers around request methods.
"""

import sys

import requests

from git_pw import config
from git_pw import logger

CONF = config.CONF
LOG = logger.LOG


def _get_auth():
    if CONF.username and CONF.password:
        return (CONF.username, CONF.password)
    else:
        LOG.error('Authentication information missing')
        LOG.error('You must configure authentication via git-config or via '
                  '--username, --password')
        sys.exit(1)


def _get_server():
    if CONF.server:
        return CONF.server.rstrip('/')
    else:
        LOG.error('Server information missing')
        LOG.error('You must provide server information via git-config or via '
                  '--server')
        sys.exit(1)


def get(url, params=None):
    """Make GET request and handle errors."""
    LOG.debug('GET %s', url)

    rsp = requests.get(url, auth=_get_auth(), params=params)
    if rsp.status_code == 403:
        LOG.error('Failed to fetch resource: Invalid credentials')
        LOG.error('Is your git-config correct?')
        sys.exit(1)
    elif rsp.status_code != 200:
        LOG.error('Failed to fetch resource: Invalid URL')
        LOG.error('Is your git-config correct?')
        sys.exit(1)

    return rsp


def put(url, data):
    """Make PUT request and handle errors."""
    LOG.debug('PUT %s, data=%r', url, data)

    rsp = requests.patch(url, auth=_get_auth(), data=data)
    if rsp.status_code == 403:
        LOG.error('Failed to update resource: Invalid credentials')
        LOG.error('Is your git-config correct?')
        sys.exit(1)
    elif rsp.status_code != 200:
        LOG.error('Failed to update resource: Invalid URL')
        LOG.error('Is your git-config correct?')
        sys.exit(1)

    return rsp.json()


def index(resource_type, params=None):
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

    return put(url, data)

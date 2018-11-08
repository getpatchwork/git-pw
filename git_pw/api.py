"""
Simple wrappers around request methods.
"""

from functools import update_wrapper
import logging
import re
import sys

import click
import requests

import git_pw
from git_pw import config

if 0:  # noqa
    from typing import Dict  # noqa
    from typing import List  # noqa
    from typing import Optional  # noqa
    from typing import Tuple  # noqa

    Filters = List[Tuple[str, str]]

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
        server = CONF.server.rstrip('/')

        if not re.match(r'.*/api/\d\.\d$', server):
            LOG.warning('Server version missing')
            LOG.warning('You should provide the server version in the URL '
                        'configured via git-config or --server')
            LOG.warning('This will be required in git-pw 2.0')

        if not re.match(r'.*/api(/\d\.\d)?$', server):
            # NOTE(stephenfin): We've already handled this particular error
            # above so we don't warn twice. We also don't stick on a version
            # number since the user clearly wants the latest
            server += '/api'

        return server
    else:
        LOG.error('Server information missing')
        LOG.error('You must provide server information via git-config or via '
                  '--server')
        sys.exit(1)


def _get_project():  # type: () -> str
    if CONF.project and CONF.project.strip() == '*':
        return ''  # just don't bother filtering on project
    elif CONF.project:
        return CONF.project.strip()
    else:
        LOG.error('Project information missing')
        LOG.error('You must provide project information via git-config or '
                  'via --project')
        LOG.error('To list all projects, set project to "*"')
        sys.exit(1)


def _handle_error(operation, exc):
    if exc.response is not None and exc.response.content:
        # server errors should always be reported
        if exc.response.status_code in range(500, 512):  # 5xx Server Error
            LOG.error('Server error. Please report this issue to '
                      'https://github.com/getpatchwork/patchwork')
            raise

        # we make the assumption that all responses will be JSON encoded
        if exc.response.status_code == 404:
            LOG.error('Resource not found')
        else:
            LOG.error(exc.response.json())
    else:
        LOG.error('Failed to %s resource. Is your configuration '
                  'correct?' % operation)
        LOG.error("Use the '--debug' flag for more information")

    if CONF.debug:
        raise
    else:
        sys.exit(1)


def version():
    # type: () -> Optional[Tuple[int, int]]
    """Get the version of the server from the URL, if present."""
    server = _get_server()

    version = re.match(r'.*/(\d)\.(\d)$', server)
    if version:
        return (int(version.group(1)), int(version.group(2)))

    # return the oldest version we support if no version provided
    return (1, 0)


def get(url, params=None, stream=False):
    # type: (str, Filters, bool) -> requests.Response
    """Make GET request and handle errors."""
    LOG.debug('GET %s', url)

    try:
        # TODO(stephenfin): We only use a subset of the types possible for
        # 'params' (namely a list of tuples) but it doesn't seem possible to
        # indicate this
        rsp = requests.get(  # type: ignore
            url, auth=_get_auth(), headers=_get_headers(), params=params,
            stream=stream)
        rsp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        _handle_error('fetch', exc)

    LOG.debug('Got response')

    return rsp


def patch(url, data):
    # type: (str, dict) -> requests.Response
    """Make PATCH request and handle errors."""
    LOG.debug('PATCH %s, data=%r', url, data)

    try:
        rsp = requests.patch(url, auth=_get_auth(), headers=_get_headers(),
                             data=data)
        rsp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        _handle_error('update', exc)

    LOG.debug('Got response')

    return rsp


def download(url, params=None):
    # type: (str, Filters) -> str
    """Retrieve a specific API resource and save it to a file.

    GET /{resource}/{resourceID}/

    The ``Content-Disposition`` header is assumed to be present and
    will be used for the output filename.

    Arguments:
        url: The resource URL.
        params: Additional parameters.

    Returns:
        A path to an output file containing the content.
    """
    rsp = get(url, params, stream=True)

    # we don't catch anything here because we should break if these are missing
    header = re.search('filename=(.+)',
                       rsp.headers.get('content-disposition') or '')
    if not header:
        LOG.error('Filename was expected but was not provided in response')
        sys.exit(1)

    output_path = header.group(1)

    with open(output_path, 'wb') as output_file:
        LOG.debug('Saving to %s', output_path)
        # we use iter_content because patches can be binary
        for block in rsp.iter_content(1024):
            output_file.write(block)

    return output_path


def index(resource_type, params=None):
    # type: (str, Filters) -> dict
    """List API resources.

    GET /{resource}/

    All resources are JSON bodies, thus we can access them in a similar
    fashion.

    Arguments:
        resource_type: The resource endpoint name.
        params: Additional parameters, filters.

    Returns:
        A list of dictionaries, representing the summary view of each resource.
    """
    # NOTE(stephenfin): All resources must have a trailing '/'
    url = '/'.join([_get_server(), resource_type, ''])

    # NOTE(stephenfin): Not all endpoints in the Patchwork API allow filtering
    # by project, but all the ones we care about here do.
    params = params or []
    params.append(('project', _get_project()))

    return get(url, params).json()


def detail(resource_type, resource_id, params=None):
    # type: (str, int, Filters) -> Dict
    """Retrieve a specific API resource.

    GET /{resource}/{resourceID}/

    Arguments:
        resource_type: The resource endpoint name.
        resource_id: The ID for the specific resource.
        params: Additional parameters.

    Returns:
        A dictionary representing the detailed view of a given resource.
    """
    # NOTE(stephenfin): All resources must have a trailing '/'
    url = '/'.join([_get_server(), resource_type, str(resource_id), ''])

    return get(url, params, stream=False).json()


def update(resource_type, resource_id, data):
    # type: (str, int, dict) -> dict
    """Update a specific API resource.

    PATCH /{resource}/{resourceID}/

    Arguments:
        resource_type: The resource endpoint name.
        resource_id: The ID for the specific resource.
        params: Fields to update.

    Returns:
        A dictionary representing the detailed view of a given resource.
    """
    # NOTE(stephenfin): All resources must have a trailing '/'
    url = '/'.join([_get_server(), resource_type, str(resource_id), ''])

    return patch(url, data).json()


def validate_multiple_filter_support(f):

    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if version() >= (1, 1):
            return ctx.invoke(f, *args, **kwargs)

        for param in ctx.command.params:
            if not param.multiple:
                continue

            if param.name in ('headers'):
                continue

            value = list(kwargs[param.name] or [])
            if value and len(value) > 1 and value != param.default:
                msg = ('The `--%s` filter was specified multiple times. '
                       'Filtering by multiple %ss is not supported with API '
                       'version 1.0. If the server supports it, use version '
                       '1.1 instead. Refer to https://git.io/vN3vX for more '
                       'information.')

                LOG.warning(msg, param.name, param.name)

        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


def retrieve_filter_ids(resource_type, filter_name, filter_value):
    """Retrieve IDs for items passed through by filter.

    Some filters require client-side filtering, e.g. filtering patches by
    submitter names.

    Arguments:
        resource_type: The filter's resource endpoint name.
        filter_name: The name of the filter.
        filter_value: The value of the filter.

    Returns:
        A list of querystring key-value pairs to use in the actual request.
    """
    if len(filter_value) < 3:
        # protect agaisnt really generic (and essentially meaningless) queries
        LOG.error('Filters must be at least 3 characters long')
        sys.exit(1)

    # NOTE(stephenfin): This purposefully ignores the possiblity of a second
    # page because it's unlikely and likely unnecessary
    items = index(resource_type, [('q', filter_value)])
    if len(items) == 0:
        LOG.warning('No matching %s found: %s', filter_name, filter_value)
    elif len(items) > 1 and version() < (1, 1):
        # we don't support multiple filters in 1.0
        msg = ('More than one match for found for `--%s=%s`. '
               'Filtering by multiple %ss is not supported with '
               'API version 1.0. If the server supports it, use '
               'version 1.1 instead. Refer to https://git.io/vN3vX '
               'for more information.')

        LOG.warning(msg, filter_name, filter_value, filter_name)

    return [(filter_name, item['id']) for item in items]

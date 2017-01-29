"""
TODO.
"""

import subprocess
import sys

import click
import requests
from tabulate import tabulate

from git_pw import config
from git_pw import logger

CONF = config.CONF
LOG = logger.LOG


@click.group()
@click.option('--debug', default=False, is_flag=True,
              help="Output more information about what's going on.")
def cli(debug):
    """Interact with Patchwork instance."""
    logger.configure_verbosity(debug)


def _get_data(url):
    """Make GET request and handle errors."""
    LOG.debug('Fetching: %s', url)

    rsp = requests.get(url, auth=(CONF.username, CONF.password))
    if rsp.status_code == 403:
        LOG.error('Failed to fetch resource: Invalid credentials')
        LOG.error('Is your git-config correct?')
        sys.exit(1)
    elif rsp.status_code != 200:
        LOG.error('Failed to fetch resource: Invalid URL')
        LOG.error('Is your git-config correct?')
        sys.exit(1)

    return rsp


def _patch_data(url, data):
    """Make PUT request and handle errors."""
    LOG.debug('Putting: %s, data=%r', url, data)

    rsp = requests.patch(url, auth=(CONF.username, CONF.password), data=data)
    if rsp.status_code == 403:
        LOG.error('Failed to update resource: Invalid credentials')
        LOG.error('Is your git-config correct?')
        sys.exit(1)
    elif rsp.status_code != 200:
        LOG.error('Failed to update resource: Invalid URL')
        LOG.error('Is your git-config correct?')
        sys.exit(1)

    return rsp


@click.command(name='apply')
@click.argument('patch_id', type=click.INT)
@click.option('--series', type=click.INT, metavar='SERIES',
              help='Series to include dependencies from. Defaults to latest.')
@click.option('--deps/--no-deps', default=True,
              help='When applying the patch, include dependencies if '
              'available. Defaults to using the most recent series.')
def apply_cmd(patch_id, series, deps):
    """Apply patch.

    Apply a patch locally using the 'git-am' command.
    """
    LOG.info('Applying patch: id=%d, series=%s, deps=%r', patch_id, series,
             deps)

    server = CONF.server.rstrip('/')
    url = '/'.join([server, 'patch', str(patch_id), 'mbox'])
    if deps:
        url += '?include_deps'

    rsp = _get_data(url)

    p = subprocess.Popen(['git', 'am', '-3'], stdin=subprocess.PIPE)
    p.communicate(rsp.content)


@click.command(name='download')
@click.argument('patch_id', type=click.INT)
@click.option('--diff', 'fmt', flag_value='raw', default=True,
              help='Show patch in diff format.')
@click.option('--mbox', 'fmt', flag_value='mbox',
              help='Show patch in mbox format.')
def download_cmd(patch_id, fmt):
    """Download a patch diff/mbox.

    Download a patch but do not apply it.
    """
    LOG.info('Downloading patch: id=%d, format=%s', patch_id, fmt)

    server = CONF.server.rstrip('/')
    url = '/'.join([server, 'patch', str(patch_id), fmt])

    rsp = _get_data(url)

    click.echo_via_pager(rsp.text)


@click.command(name='show')
@click.argument('patch_id', type=click.INT)
def show_cmd(patch_id):
    """Show information about patch.

    Retrieve Patchwork metadata for a patch.
    """
    LOG.debug('Showing patch: id=%d', patch_id)

    # FIXME(stephenfin): Support the 'api_server' config value
    server = CONF.server.rstrip('/')
    url = '/'.join([server, 'api', '1.0', 'patches', str(patch_id)])

    # TODO(stephenfin): Ideally we shouldn't have to make three requests
    # to do this operation. Perhaps we should nest these fields in the
    # response
    patch = _get_data(url).json()
    submitter = _get_data(patch['submitter']).json()
    project = _get_data(patch['project']).json()
    delegate = {}
    if patch['delegate']:
        delegate = _get_data(patch['delegate']).json()

    output = [
        ('ID', patch.get('id')),
        ('Message ID', patch.get('msgid')),
        ('Date', patch.get('date')),
        ('Name', patch.get('name')),
        ('Submitter', '%s (%s)' % (
            submitter.get('name'), submitter.get('email'))),
        ('State', patch.get('state')),
        ('Archived', patch.get('archived')),
        ('Project', project.get('name')),
        ('Delegate', delegate.get('username')),
        ('Commit Ref', patch.get('commit_ref'))]

    # TODO(stephenfin): We might want to make this machine readable?
    click.echo(tabulate(output, ['Property', 'Value'], tablefmt='psql'))


@click.command(name='update')
@click.argument('patch_id', type=click.INT)
@click.option('--commit-ref', metavar='COMMIT_REF',
              help='Set the patch commit reference hash')
@click.option('--state', metavar='STATE',
              help='Set the patch state. Should be a slugified representation '
              'of a state. The available states are instance dependant.')
@click.option('--delegate', metavar='DELEGATE',
              help='Set the patch delegate. Should be unique user identifier: '
              'either a username or a user\'s email address.')
@click.option('--archived', metavar='ARCHIVED', type=click.BOOL,
              help='Set the patch archived state.')
def update_cmd(patch_id, commit_ref, state, delegate, archived):
    """Update a patch.

    Updates a Patch on the Patchwork instance. Some operations may
    require admin or maintainer permissions.
    """
    LOG.info('Updating patch: id=%d, commit_ref=%s, state=%s, archived=%s',
             patch_id, commit_ref, state, archived)

    # FIXME(stephenfin): Support the 'api_server' config value
    server = CONF.server.rstrip('/')

    if delegate:
        url = '/'.join([server, 'api', '1.0', 'users', '?q=%s' % delegate])
        users = _get_data(url).json()
        if len(users) == 0:
            LOG.error('No matching delegates found: %s', delegate)
            sys.exit(1)
        elif len(users) > 1:
            LOG.error('More than one delegate found: %s', delegate)
            sys.exit(1)

        delegate = users[0]['id']

    url = '/'.join([server, 'api', '1.0', 'patches', str(patch_id), ''])
    data = {}
    for key, value in [('commit_ref', commit_ref), ('state', state),
                       ('archived', archived), ('delegate', delegate)]:
        if value is None:
            continue

        data[key] = str(value)

    patch = _patch_data(url, data).json()

    # TODO(stephenfin): Ideally we shouldn't have to make three requests
    # to do this operation. Perhaps we should nest these fields in the
    # response
    submitter = _get_data(patch['submitter']).json()
    project = _get_data(patch['project']).json()
    if not delegate:
        delegate = {}
        if patch['delegate']:
            delegate = _get_data(patch['delegate']).json()

    output = [
        ('ID', patch.get('id')),
        ('Message ID', patch.get('msgid')),
        ('Date', patch.get('date')),
        ('Name', patch.get('name')),
        ('Submitter', '%s (%s)' % (
            submitter.get('name'), submitter.get('email'))),
        ('State', patch.get('state')),
        ('Archived', patch.get('archived')),
        ('Project', project.get('name')),
        ('Delegate', delegate.get('username')),
        ('Commit Ref', patch.get('commit_ref'))]

    # TODO(stephenfin): We might want to make this machine readable?
    click.echo(tabulate(output, ['Property', 'Value'], tablefmt='psql'))


@click.command(name='list')
@click.option('--state', metavar='STATE', multiple=True,
              help='Show only patches matching these states. Should be '
              'slugified representations of states. The available states '
              'are instance dependant.')
@click.option('--submitter', metavar='SUBMITTER', multiple=True,
              help='Show only patches by these submitters. Should be an '
              'email or name.')
@click.option('--delegate', metavar='DELEGATE', multiple=True,
              help='Show only patches by these delegates. Should be an '
              'email or username.')
@click.option('--archived', default=False, is_flag=True,
              help='Include patches that are archived.')
def list_cmd(state, submitter, delegate, archived):
    """List patches.

    List patches on the Patchwork instance.
    """
    LOG.info('List patches: states=%s, submitters=%s, delegates=%s, '
             'archived=%r', ','.join(state), ','.join(submitter),
             ','.join(delegate), archived)

    # FIXME(stephenfin): Support the 'api_server' config value
    server = CONF.server.rstrip('/')

    # Generate filter strings

    # TODO(stephenfin): It should be possible to filter patches by project
    # using the project list-id, submitters by email
    submitter_filters = []
    for subm in submitter:
        url = '/'.join([server, 'api', '1.0', 'people', '?q=%s' % subm])
        people = _get_data(url).json()
        if len(people) == 0:
            LOG.error('No matching submitter found: %s', subm)
            sys.exit(1)
        elif len(people) > 1:
            LOG.error('More than one submitter found: %s', subm)
            sys.exit(1)

        submitter_filters.append('submitter=%d' % people[0]['id'])

    delegate_filters = []
    for delg in delegate:
        url = '/'.join([server, 'api', '1.0', 'users', '?q=%s' % delg])
        users = _get_data(url).json()
        if len(users) == 0:
            LOG.error('No matching delegates found: %s', delg)
            sys.exit(1)
        elif len(users) > 1:
            LOG.error('More than one delegate found: %s', delg)
            sys.exit(1)

        delegate_filters.append('delegate=%s' % users[0]['id'])

    url = '/'.join([server, 'api', '1.0', 'projects', CONF.project])
    project_filter = 'project=%d' % _get_data(url).json()['id']

    # TODO(stephenfin): Perhaps we could use string values. Refer to
    # https://github.com/carltongibson/django-filter/pull/378
    archived_filter = 'archived=%d' % (3 if archived else 1)

    # FIXME(stephenfin): We're not currently supporting pagination. We must
    # fix this.
    qs = '&'.join(submitter_filters + delegate_filters + [archived_filter,
                                                          project_filter])
    url = '/'.join([server, 'api', '1.0', 'patches', '?%s' % qs])
    patches = _get_data(url).json()

    # Fetch matching users/people

    people = {}
    users = {}

    for patch in patches:
        if patch['submitter'] not in people:
            subm = _get_data(patch['submitter']).json()
            people[patch['submitter']] = '%s (%s)' % (
                subm.get('name'), subm.get('email'))

        patch['submitter'] = people[patch['submitter']]

        if patch['delegate'] and patch['delegate'] not in users:
            delg = _get_data(patch['delegate']).json()
            users[patch['delegate']] = delg.get('username')
        elif not patch['delegate']:
            continue

        patch['delegate'] = users[patch['delegate']]

    # Format and print output

    headers = ['ID', 'Date', 'Name', 'Submitter', 'State', 'Archived',
               'Delegate', 'Commit Ref']

    output = [[
        patch.get('id'),
        patch.get('date'),
        patch.get('name'),
        patch.get('submitter'),
        patch.get('state'),
        patch.get('archived'),
        patch.get('delegate'),
        patch.get('commit_ref'),
    ] for patch in patches]

    click.echo(tabulate(output, headers, tablefmt='psql'))


cli.add_command(apply_cmd)
cli.add_command(show_cmd)
cli.add_command(download_cmd)
cli.add_command(update_cmd)
cli.add_command(list_cmd)

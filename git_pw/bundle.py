"""
Bundle subcommands.
"""

import subprocess
import sys

import click
from tabulate import tabulate

from git_pw import api
from git_pw import config
from git_pw import logger
from git_pw import utils

CONF = config.CONF
LOG = logger.LOG


@click.command(name='apply')
@click.argument('bundle_id', type=click.INT)
def apply_cmd(bundle_id):
    """Apply bundle.

    Apply a bundle locally using the 'git-am' command.
    """
    LOG.info('Applying bundle: id=%d', bundle_id)

    bundle = api.detail('bundles', bundle_id)
    mbox = api.get(bundle['mbox']).text

    p = subprocess.Popen(['git', 'am', '-3'], stdin=subprocess.PIPE)
    p.communicate(mbox)


@click.command(name='download')
@click.argument('bundle_id', type=click.INT)
def download_cmd(bundle_id):
    """Download bundle in mbox format.

    Download a bundle but do not apply it.
    """
    LOG.info('Downloading bundle: id=%d', bundle_id)

    bundle = api.detail('bundles', bundle_id)
    output = api.get(bundle['mbox']).text

    click.echo_via_pager(output)


@click.command(name='show')
@click.argument('bundle_id', type=click.INT)
def show_cmd(bundle_id):
    """Show information about bundle.

    Retrieve Patchwork metadata for a bundle.
    """
    LOG.debug('Showing bundle: id=%d', bundle_id)

    bundle = api.detail('bundles', bundle_id)
    owner = api.get(bundle['owner']).json()
    project = api.get(bundle['project']).json()

    output = [
        ('ID', bundle.get('id')),
        ('Name', bundle.get('name')),
        ('Owner', owner.get('username')),
        ('Project', project.get('name')),
        ('Public', bundle.get('public'))]

    # TODO(stephenfin): We might want to make this machine readable?
    click.echo(tabulate(output, ['Property', 'Value'], tablefmt='psql'))


@click.command(name='list')
@click.option('--owner', metavar='OWNER', multiple=True,
              help='Show only bundles with these owners. Should be an email '
              'or name. Private bundles of other users will not be shown.')
@click.option('--limit', metavar='LIMIT', type=click.INT,
              help='Maximum number of bundles to show.')
@click.option('--page', metavar='PAGE', type=click.INT,
              help='Page to retrieve bundles from. This is influenced by the '
              'size of LIMIT.')
@click.option('--sort', metavar='FIELD', default='name', type=click.Choice(
                  ['id', '-id', 'name', '-name']),
              help='Sort output on given field.')
def list_cmd(owner, limit, page, sort):
    """List bundles.

    List bundles on the Patchwork instance.
    """
    LOG.info('List bundles: owners=%s, limit=%r, page=%r, sort=%r',
             ','.join(owner), limit, page, sort)

    params = []

    # TODO(stephenfin): It should be possible to filter bundles by project
    # using the project list-id, owners by email
    for own in owner:
        users = api.index('users', {'q': own})
        if len(users) == 0:
            LOG.error('No matching owner found: %s', own)
            sys.exit(1)
        elif len(users) > 1:
            LOG.error('More than one owner found: %s', own)
            sys.exit(1)

        params.append(('owner', users[0]['id']))

    project = api.detail('projects', CONF.project)

    params.extend([
        ('project', project['id']),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    bundles = api.index('bundles', params)

    # Fetch matching users

    users = {}

    for bundle in bundles:
        if bundle['owner'] not in users:
            own = api.get(bundle['owner']).json()
            users[bundle['owner']] = own.get('username')

        bundle['owner'] = users[bundle['owner']]

    # Format and print output

    headers = ['ID', 'Name', 'Owner', 'Public']

    output = [[
        bundle.get('id'),
        utils.trim(bundle.get('name') or ''),
        bundle.get('owner'),
        'yes' if bundle.get('public') else 'no',
    ] for bundle in bundles]

    click.echo_via_pager(tabulate(output, headers, tablefmt='psql'))

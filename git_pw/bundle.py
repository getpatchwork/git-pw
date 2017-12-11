"""
Bundle subcommands.
"""

import logging
import sys

import click
from tabulate import tabulate

from git_pw import api
from git_pw import utils

LOG = logging.getLogger(__name__)


@click.command(name='apply')
@click.argument('bundle_id', type=click.INT)
@click.argument('args', nargs=-1)
def apply_cmd(bundle_id, args):
    """Apply bundle.

    Apply a bundle locally using the 'git-am' command.
    """
    LOG.info('Applying bundle: id=%d', bundle_id)

    bundle = api.detail('bundles', bundle_id)
    mbox = api.download(bundle['mbox']).text

    utils.git_am(mbox, args)


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

    def _format_patch(patch):
        return '%-4d %s' % (patch.get('id'), patch.get('name'))

    output = [
        ('ID', bundle.get('id')),
        ('Name', bundle.get('name')),
        ('Owner', bundle.get('owner').get('username')),
        ('Project', bundle.get('project').get('name')),
        ('Public', bundle.get('public'))]

    prefix = 'Patches'
    for patch in bundle.get('patches'):
        output.append((prefix, _format_patch(patch)))
        prefix = ''

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
@click.argument('name', required=False)
def list_cmd(owner, limit, page, sort, name):
    """List bundles.

    List bundles on the Patchwork instance.
    """
    LOG.info('List bundles: owners=%s, limit=%r, page=%r, sort=%r',
             ','.join(owner), limit, page, sort)

    params = []

    # TODO(stephenfin): It should be possible to filter bundles by owner email
    for own in owner:
        users = api.index('users', {'q': own})
        if len(users) == 0:
            LOG.error('No matching owner found: %s', own)
            sys.exit(1)
        elif len(users) > 1:
            LOG.error('More than one owner found: %s', own)
            sys.exit(1)

        params.append(('owner', users[0]['id']))

    params.extend([
        ('q', name),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    bundles = api.index('bundles', params)

    # Format and print output

    headers = ['ID', 'Name', 'Owner', 'Public']

    output = [[
        bundle.get('id'),
        utils.trim(bundle.get('name') or ''),
        bundle.get('owner').get('username'),
        'yes' if bundle.get('public') else 'no',
    ] for bundle in bundles]

    click.echo_via_pager(tabulate(output, headers, tablefmt='psql'))

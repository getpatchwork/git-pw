"""
Bundle subcommands.
"""

import logging
import sys

import click

from git_pw import api
from git_pw import utils

LOG = logging.getLogger(__name__)

_list_headers = ('ID', 'Name', 'Owner', 'Public')
_sort_fields = ('id', '-id', 'name', '-name')


def _get_bundle(bundle_id):
    """Fetch bundle by ID or name.

    Allow users to provide a string to search for bundles. This doesn't make
    sense to expose via the API since there's no uniqueness constraint on
    bundle names.
    """
    if bundle_id.isdigit():
        return api.detail('bundles', bundle_id)

    bundles = api.index('bundles', [('q', bundle_id)])
    if len(bundles) == 0:
        LOG.error('No matching bundle found: %s', bundle_id)
        sys.exit(1)
    elif len(bundles) > 1:
        LOG.error('More than one bundle found: %s', bundle_id)
        sys.exit(1)

    return bundles[0]


@click.command(name='apply', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('bundle_id')
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def apply_cmd(bundle_id, args):
    """Apply bundle.

    Apply a bundle locally using the 'git-am' command. Any additional ARGS
    provided will be passed to the 'git-am' command.
    """
    LOG.debug('Applying bundle: id=%s', bundle_id)

    bundle = _get_bundle(bundle_id)
    mbox = api.download(bundle['mbox'])

    utils.git_am(mbox, args)


@click.command(name='download')
@click.argument('bundle_id')
@click.argument('output', type=click.File('wb'), required=False)
def download_cmd(bundle_id, output):
    """Download bundle in mbox format.

    Download a bundle but do not apply it. ``OUTPUT`` is optional and can be an
    output path or ``-`` to output to ``stdout``. If ``OUTPUT`` is not
    provided, the output path will be automatically chosen.
    """
    LOG.debug('Downloading bundle: id=%s', bundle_id)

    path = None
    bundle = _get_bundle(bundle_id)

    if output:
        output.write(api.get(bundle['mbox']).text)

        if output != sys.stdout:
            path = output.name
    else:
        path = api.download(bundle['mbox'])

    if path:
        LOG.info('Downloaded bundle to %s', path)


@click.command(name='show')
@utils.format_options
@click.argument('bundle_id')
def show_cmd(fmt, bundle_id):
    """Show information about bundle.

    Retrieve Patchwork metadata for a bundle.
    """
    LOG.debug('Showing bundle: id=%s', bundle_id)

    bundle = _get_bundle(bundle_id)

    def _format_patch(patch):
        return '%-4d %s' % (patch.get('id'), patch.get('name'))

    output = [
        ('ID', bundle.get('id')),
        ('Name', bundle.get('name')),
        ('URL', bundle.get('web_url')),
        ('Owner', bundle.get('owner').get('username')),
        ('Project', bundle.get('project').get('name')),
        ('Public', bundle.get('public'))]

    prefix = 'Patches'
    for patch in bundle.get('patches'):
        output.append((prefix, _format_patch(patch)))
        prefix = ''

    utils.echo(output, ['Property', 'Value'], fmt=fmt)


@click.command(name='list')
@click.option('--owner', metavar='OWNER', multiple=True,
              help='Show only bundles with these owners. Should be an email, '
              'name or ID. Private bundles of other users will not be shown.')
@utils.pagination_options(sort_fields=_sort_fields, default_sort='name')
@utils.format_options(headers=_list_headers)
@click.argument('name', required=False)
@api.validate_multiple_filter_support
def list_cmd(owner, limit, page, sort, fmt, headers, name):
    """List bundles.

    List bundles on the Patchwork instance.
    """
    LOG.debug('List bundles: owners=%s, limit=%r, page=%r, sort=%r',
              ','.join(owner), limit, page, sort)

    params = []

    for own in owner:
        # we support server-side filtering by username (but not email) in 1.1
        if (api.version() >= (1, 1) and '@' not in own) or own.isdigit():
            params.append(('owner', own))
        else:
            params.extend(api.retrieve_filter_ids('users', 'owner', own))

    params.extend([
        ('q', name),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    bundles = api.index('bundles', params)

    # Format and print output

    output = []

    for bundle in bundles:
        item = [
            bundle.get('id'),
            utils.trim(bundle.get('name') or ''),
            bundle.get('owner').get('username'),
            'yes' if bundle.get('public') else 'no',
        ]

        output.append([])
        for idx, header in enumerate(_list_headers):
            if header not in headers:
                continue

            output[-1].append(item[idx])

    utils.echo_via_pager(output, headers, fmt=fmt)

"""
Patch subcommands.
"""

import logging
import sys

import arrow
import click
from tabulate import tabulate

from git_pw import api
from git_pw import utils

LOG = logging.getLogger(__name__)


@click.command(name='apply')
@click.argument('patch_id', type=click.INT)
@click.option('--series', type=click.INT, metavar='SERIES',
              help='Series to include dependencies from. Defaults to latest.')
@click.option('--deps/--no-deps', default=True,
              help='When applying the patch, include dependencies if '
              'available. Defaults to using the most recent series.')
@click.argument('args', nargs=-1)
def apply_cmd(patch_id, series, deps, args):
    """Apply patch.

    Apply a patch locally using the 'git-am' command.
    """
    LOG.info('Applying patch: id=%d, series=%s, deps=%r, args=%s', patch_id,
             series, deps, ' '.join(args))

    patch = api.detail('patches', patch_id)

    if deps and not series:
        series = '*'
    elif not deps:
        series = None

    mbox = api.download(patch['mbox'], {'series': series})

    utils.git_am(mbox, args)


@click.command(name='download')
@click.argument('patch_id', type=click.INT)
@click.option('--diff', 'fmt', flag_value='diff',
              help='Show patch in diff format.')
@click.option('--mbox', 'fmt', flag_value='mbox', default=True,
              help='Show patch in mbox format.')
def download_cmd(patch_id, fmt):
    """Download a patch diff/mbox.

    Download a patch but do not apply it.
    """
    LOG.info('Downloading patch: id=%d, format=%s', patch_id, fmt)

    patch = api.detail('patches', patch_id)

    if fmt == 'diff':
        output = patch['diff']
    else:
        output = api.get(patch['mbox']).text

    click.echo_via_pager(output)


def _show_patch(patch):

    def _format_series(series):
        return '%-4d %s' % (series.get('id'), series.get('name') or '-')

    output = [
        ('ID', patch.get('id')),
        ('Message ID', patch.get('msgid')),
        ('Date', patch.get('date')),
        ('Name', patch.get('name')),
        ('Submitter', '%s (%s)' % (patch.get('submitter').get('name'),
                                   patch.get('submitter').get('email'))),
        ('State', patch.get('state')),
        ('Archived', patch.get('archived')),
        ('Project', patch.get('project').get('name')),
        ('Delegate', (patch.get('delegate').get('username')
                      if patch.get('delegate') else '')),
        ('Commit Ref', patch.get('commit_ref'))]

    prefix = 'Series'
    for series in patch.get('series'):
        output.append((prefix, _format_series(series)))
        prefix = ''

    # TODO(stephenfin): We might want to make this machine readable?
    click.echo(tabulate(output, ['Property', 'Value'], tablefmt='psql'))


@click.command(name='show')
@click.argument('patch_id', type=click.INT)
def show_cmd(patch_id):
    """Show information about patch.

    Retrieve Patchwork metadata for a patch.
    """
    LOG.debug('Showing patch: id=%d', patch_id)

    patch = api.detail('patches', patch_id)

    _show_patch(patch)


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

    if delegate:
        users = api.index('users', {'q': delegate})
        if len(users) == 0:
            LOG.error('No matching delegates found: %s', delegate)
            sys.exit(1)
        elif len(users) > 1:
            LOG.error('More than one delegate found: %s', delegate)
            sys.exit(1)

        delegate = users[0]['id']

    data = {}
    for key, value in [('commit_ref', commit_ref), ('state', state),
                       ('archived', archived), ('delegate', delegate)]:
        if value is None:
            continue

        data[key] = str(value)

    data = [('commit_ref', commit_ref), ('state', state),
            ('archived', archived), ('delegate', delegate)]

    patch = api.update('patches', patch_id, data)

    _show_patch(patch)


# NOTE(stephenfin): The list of default states is populated from Patchwork's
# 'fixtures/default_states.xml' file [1]. Due to bug #156, we can only
# currently filter by one state but we've configured this for future support of
# multiple states.
#
# [1] https://git.io/vN3vi
# [2] https://git.io/vN3vX
@click.command(name='list')
@click.option('--state', metavar='STATE', multiple=True,
              default=['under-review', 'new'],
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
@click.option('--limit', metavar='LIMIT', type=click.INT,
              help='Maximum number of patches to show.')
@click.option('--page', metavar='PAGE', type=click.INT,
              help='Page to retrieve patches from. This is influenced by the '
              'size of LIMIT.')
@click.option('--sort', metavar='FIELD', default='-date', type=click.Choice(
                  ['id', '-id', 'name', '-name', 'date', '-date']),
              help='Sort output on given field.')
@click.argument('name', required=False)
def list_cmd(state, submitter, delegate, archived, limit, page, sort, name):
    """List patches.

    List patches on the Patchwork instance.
    """
    LOG.info('List patches: states=%s, submitters=%s, delegates=%s, '
             'archived=%r', ','.join(state), ','.join(submitter),
             ','.join(delegate), archived)

    params = []

    for state in state:
        params.append(('state', state))

    # TODO(stephenfin): It should be possible to filter patches submitter email
    for subm in submitter:
        people = api.index('people', {'q': subm})
        if len(people) == 0:
            LOG.error('No matching submitter found: %s', subm)
            sys.exit(1)
        elif len(people) > 1:
            LOG.error('More than one submitter found: %s', subm)
            sys.exit(1)

        params.append(('submitter', people[0]['id']))

    for delg in delegate:
        users = api.index('users', {'q': delg})
        if len(users) == 0:
            LOG.error('No matching delegates found: %s', delg)
            sys.exit(1)
        elif len(users) > 1:
            LOG.error('More than one delegate found: %s', delg)
            sys.exit(1)

        params.append(('delegate', users[0]['id']))

    params.extend([
        ('q', name),
        # TODO(stephenfin): Perhaps we could use string values. Refer to
        # https://github.com/carltongibson/django-filter/pull/378
        ('archived', 3 if archived else 1),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    patches = api.index('patches', params)

    # Format and print output

    headers = ['ID', 'Date', 'Name', 'Submitter', 'State', 'Archived',
               'Delegate']

    output = [[
        patch.get('id'),
        arrow.get(patch.get('date')).humanize(),
        utils.trim(patch.get('name')),
        '%s (%s)' % (patch.get('submitter').get('name'),
                     patch.get('submitter').get('email')),
        patch.get('state'),
        'yes' if patch.get('archived') else 'no',
        (patch.get('delegate').get('username')
         if patch.get('delegate') else ''),
    ] for patch in patches]

    click.echo_via_pager(tabulate(output, headers, tablefmt='psql'))

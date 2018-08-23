"""
Series subcommands.
"""

import logging
import sys

import arrow
import click
from tabulate import tabulate

from git_pw import api
from git_pw import utils

LOG = logging.getLogger(__name__)


@click.command(name='apply', context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('series_id', type=click.INT)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def apply_cmd(series_id, args):
    """Apply series.

    Apply a series locally using the 'git-am' command. Any additional ARGS
    provided will be passed to the 'git-am' command.
    """
    LOG.debug('Applying series: id=%d, args=%s', series_id, ' '.join(args))

    series = api.detail('series', series_id)
    mbox = api.download(series['mbox'])

    utils.git_am(mbox, args)


@click.command(name='download')
@click.argument('series_id', type=click.INT)
@click.argument('output', type=click.File('wb'), required=False)
def download_cmd(series_id, output):
    """Download series in mbox format.

    Download a series but do not apply it. ``OUTPUT`` is optional and can be an
    output path or ``-`` to output to ``stdout``. If ``OUTPUT`` is not
    provided, the output path will be automatically chosen.
    """
    LOG.debug('Downloading series: id=%d', series_id)

    path = None
    series = api.detail('series', series_id)

    if output:
        output.write(api.get(series['mbox']).text)

        if output != sys.stdout:
            path = output.name
    else:
        path = api.download(series['mbox'])

    if path:
        LOG.info('Downloaded series to %s', path)


@click.command(name='show')
@click.argument('series_id', type=click.INT)
def show_cmd(series_id):
    """Show information about series.

    Retrieve Patchwork metadata for a series.
    """
    LOG.debug('Showing series: id=%d', series_id)

    series = api.detail('series', series_id)

    def _format_submission(submission):
        return '%-4d %s' % (submission.get('id'), submission.get('name'))

    output = [
        ('ID', series.get('id')),
        ('Date', series.get('date')),
        ('Name', series.get('name')),
        ('URL', series.get('web_url')),
        ('Submitter', '%s (%s)' % (series.get('submitter').get('name'),
                                   series.get('submitter').get('email'))),
        ('Project', series.get('project').get('name')),
        ('Version', series.get('version')),
        ('Received', '%d of %d' % (series.get('received_total'),
                                   series.get('total'))),
        ('Complete', series.get('received_all')),
        ('Cover', (_format_submission(series.get('cover_letter'))
                   if series.get('cover_letter') else ''))]

    prefix = 'Patches'
    for patch in series.get('patches'):
        output.append((prefix, _format_submission(patch)))
        prefix = ''

    # TODO(stephenfin): We might want to make this machine readable?
    click.echo(tabulate(output, ['Property', 'Value'], tablefmt='psql'))


@click.command(name='list')
@click.option('--submitter', metavar='SUBMITTER', multiple=True,
              help='Show only series by these submitters. Should be an '
              'email or name.')
@click.option('--limit', metavar='LIMIT', type=click.INT,
              help='Maximum number of series to show.')
@click.option('--page', metavar='PAGE', type=click.INT,
              help='Page to retrieve series from. This is influenced by the '
              'size of LIMIT.')
@click.option('--sort', metavar='FIELD', default='-date', type=click.Choice(
                  ['id', '-id', 'name', '-name', 'date', '-date']),
              help='Sort output on given field.')
@click.argument('name', required=False)
@api.validate_multiple_filter_support
def list_cmd(submitter, limit, page, sort, name):
    """List series.

    List series on the Patchwork instance.
    """
    LOG.debug('List series: submitters=%s, limit=%r, page=%r, sort=%r',
              ','.join(submitter), limit, page, sort)

    params = []

    if api.version() >= (1, 1):
        params.extend([('submitter', subm) for subm in submitter])
    else:
        for subm in submitter:
            people = api.index('people', [('q', subm)])
            if len(people) == 0:
                LOG.error('No matching submitter found: %s', subm)
                sys.exit(1)
            elif len(people) > 1:
                LOG.error('More than one submitter found: %s', subm)
                sys.exit(1)

            params.append(('submitter', people[0]['id']))

    params.extend([
        ('q', name),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    series = api.index('series', params)

    # Format and print output

    headers = ['ID', 'Date', 'Name', 'Version', 'Submitter']

    output = [[
        series_.get('id'),
        arrow.get(series_.get('date')).humanize(),
        utils.trim(series_.get('name') or ''),
        series_.get('version'),
        '%s (%s)' % (series_.get('submitter').get('name'),
                     series_.get('submitter').get('email'))
    ] for series_ in series]

    utils.echo_via_pager(tabulate(output, headers, tablefmt='psql'))

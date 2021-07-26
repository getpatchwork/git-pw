"""
Series subcommands.
"""

import logging

import arrow
import click

from git_pw import api
from git_pw import utils
import os.path
import sys

LOG = logging.getLogger(__name__)

_list_headers = ('ID', 'Date', 'Name', 'Version', 'Submitter')
_sort_fields = ('id', '-id', 'name', '-name', 'date', '-date')


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
@click.argument(
    'output',
    type=click.Path(file_okay=True, writable=True, readable=True),
    required=False,
)
@click.option(
    '--separate', 'fmt', flag_value='separate',
    help='Download each series patch to a separate file',
)
@click.option(
    '--combined', 'fmt', flag_value='combined', default=True,
    help='Download all series patches to one file',
)
def download_cmd(series_id, output, fmt):
    """Download series in mbox format.

    Download a series but do not apply it. ``OUTPUT`` is optional and can be an
    output path or ``-`` to output to ``stdout``. If ``OUTPUT`` is not
    provided, the output path will be automatically chosen.
    """
    LOG.debug('Downloading series: id=%d', series_id)

    path = None
    series = api.detail('series', series_id)

    if fmt == 'separate':
        if output and not os.path.isdir(output):
            LOG.error(
                'When downloading into separate files, OUTPUT can only be a '
                'directoy'
            )
            sys.exit(1)

        for patch in series.get('patches'):
            path = api.download(patch['mbox'], output=output)
            if path:
                LOG.info(
                    'Downloaded patch %s from series %s to %s',
                    patch.get('id'), series.get('id'), path,
                )
        return

    path = api.download(series['mbox'], output=output)

    if path:
        LOG.info('Downloaded series to %s', path)


@click.command(name='show')
@utils.format_options
@click.argument('series_id', type=click.INT)
def show_cmd(fmt, series_id):
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

    utils.echo(output, ['Property', 'Value'], fmt=fmt)


@click.command(name='list')
@click.option('--submitter', 'submitters', metavar='SUBMITTER', multiple=True,
              help='Show only series by these submitters. Should be an '
              'email, name or ID.')
@utils.pagination_options(sort_fields=_sort_fields, default_sort='-date')
@utils.format_options(headers=_list_headers)
@click.argument('name', required=False)
@api.validate_multiple_filter_support
def list_cmd(submitters, limit, page, sort, fmt, headers, name):
    """List series.

    List series on the Patchwork instance.
    """
    LOG.debug('List series: submitters=%s, limit=%r, page=%r, sort=%r',
              ','.join(submitters), limit, page, sort)

    params = []

    for submitter in submitters:
        if submitter.isdigit():
            params.append(('submitter', submitter))
        else:
            # we support server-side filtering by email (but not name) in 1.1
            if api.version() >= (1, 1) and '@' in submitter:
                params.append(('submitter', submitter))
            else:
                params.extend(
                    api.retrieve_filter_ids('people', 'submitter', submitter))

    params.extend([
        ('q', name),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    series = api.index('series', params)

    # Format and print output

    output = []

    for series_ in series:
        item = [
            series_.get('id'),
            arrow.get(series_.get('date')).humanize(),
            utils.trim(series_.get('name') or ''),
            series_.get('version'),
            '%s (%s)' % (series_.get('submitter').get('name'),
                         series_.get('submitter').get('email'))
        ]

        output.append([])
        for idx, header in enumerate(_list_headers):
            if header not in headers:
                continue

            output[-1].append(item[idx])

    utils.echo_via_pager(output, headers, fmt=fmt)

"""
Series subcommands.
"""

import subprocess
import sys

import arrow
import click
from tabulate import tabulate

from git_pw import api
from git_pw import config
from git_pw import logger
from git_pw import utils

CONF = config.CONF
LOG = logger.LOG


@click.command(name='apply')
@click.argument('series_id', type=click.INT)
@click.argument('args', nargs=-1)
def apply_cmd(series_id, args):
    """Apply series.

    Apply a series locally using the 'git-am' command.
    """
    LOG.info('Applying series: id=%d, args=%s', series_id, ' '.join(args))

    series = api.detail('series', series_id)
    mbox = api.get(series['mbox']).text

    cmd = ['git', 'am']
    if args:
        cmd.extend(args)
    else:
        cmd.append('-3')

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(mbox)


@click.command(name='download')
@click.argument('series_id', type=click.INT)
def download_cmd(series_id):
    """Download series in mbox format.

    Download a series but do not apply it.
    """
    LOG.info('Downloading series: id=%d', series_id)

    series = api.detail('series', series_id)
    output = api.get(series['mbox']).text

    click.echo_via_pager(output)


@click.command(name='show')
@click.argument('series_id', type=click.INT)
def show_cmd(series_id):
    """Show information about series.

    Retrieve Patchwork metadata for a series.
    """
    LOG.debug('Showing series: id=%d', series_id)

    series = api.detail('series', series_id)
    submitter = api.get(series['submitter']).json()
    project = api.get(series['project']).json()

    output = [
        ('ID', series.get('id')),
        ('Date', series.get('date')),
        ('Name', series.get('name')),
        ('Submitter', '%s (%s)' % (
            submitter.get('name'), submitter.get('email'))),
        ('Project', project.get('name'))]

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
def list_cmd(submitter, limit, page, sort, name):
    """List series.

    List series on the Patchwork instance.
    """
    LOG.info('List series: submitters=%s, limit=%r, page=%r, sort=%r',
             ','.join(submitter), limit, page, sort)

    params = []

    # TODO(stephenfin): It should be possible to filter series by project
    # using the project list-id, submitters by email
    for subm in submitter:
        people = api.index('people', {'q': subm})
        if len(people) == 0:
            LOG.error('No matching submitter found: %s', subm)
            sys.exit(1)
        elif len(people) > 1:
            LOG.error('More than one submitter found: %s', subm)
            sys.exit(1)

        params.append(('submitter', people[0]['id']))

    project = api.detail('projects', CONF.project)

    params.extend([
        ('q', name),
        ('project', project['id']),
        ('page', page),
        ('per_page', limit),
        ('order', sort),
    ])

    series = api.index('series', params)

    # Fetch matching users/people

    people = {}

    for series_ in series:
        if series_['submitter'] not in people:
            subm = api.get(series_['submitter']).json()
            people[series_['submitter']] = '%s (%s)' % (
                subm.get('name'), subm.get('email'))

        series_['submitter'] = people[series_['submitter']]

    # Format and print output

    headers = ['ID', 'Date', 'Name', 'Version', 'Submitter']

    output = [[
        series_.get('id'),
        arrow.get(series_.get('date')).humanize(),
        utils.trim(series_.get('name') or ''),
        series_.get('version'),
        series_.get('submitter'),
    ] for series_ in series]

    click.echo_via_pager(tabulate(output, headers, tablefmt='psql'))

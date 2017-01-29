"""
TODO.
"""

import subprocess
import sys

import click
import requests

from git_pw import config

CONF = config.CONF


@click.group()
def cli():
    """Interact with Patchwork instance."""
    pass


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
    click.echo('Apply patch %d (series=%s, deps=%r)' % (
        patch_id, series, deps))

    server = CONF.server.rstrip('/')
    url = '/'.join([server, 'patch', str(patch_id), 'mbox'])
    if deps:
        url += '?include_deps'

    rsp = requests.get(url)
    if rsp.status_code != 200:
        click.echo('Failed to fetch patch. Is the URL correct?')
        sys.exit(1)

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

    Download a patch but do not apply it."""
    click.echo('Download patch %d (format=%s)' % (patch_id, fmt))

    server = CONF.server.rstrip('/')
    url = '/'.join([server, 'patch', str(patch_id), fmt])

    click.echo(url)

    rsp = requests.get(url)
    if rsp.status_code != 200:
        click.echo('Failed to fetch patch. Is the URL correct?')
        sys.exit(1)

    click.echo_via_pager(rsp.text)


@click.command(name='show')
@click.argument('patch_id', type=click.INT)
def show_cmd(patch_id):
    """Show information about patch.

    Retrieve Patchwork metadata for a patch.
    """
    click.echo('Show patch %d' % (patch_id))


@click.command(name='update')
@click.argument('patch_id', type=click.INT)
@click.option('--commit-ref', metavar='COMMIT_REF',
              help='Set the patch commit reference hash')
@click.option('--state', metavar='STATE',
              help='Set the patch state. Should be a slugified representation '
              'of a state. The available states are instance dependant.')
@click.option('--archived', metavar='ARCHIVED', type=click.BOOL,
              help='Set the patch archived state.')
def update_cmd(patch_id, commit_ref, state, archived):
    """Update a patch.

    Updates a Patch on the Patchwork instance. Some operations may
    require admin or maintainer permissions.
    """
    click.echo('Update patch %d (commit_ref=%s, state=%s, archived=%s)' % (
        patch_id, commit_ref, state, archived))


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
@click.option('--archived/--no-archived', default=False,
              help='Show only patches that are archived.')
def list_cmd(state, submitter, delegate, archived):
    """List patches.

    List patches on the Patchwork instance.
    """
    click.echo('List patches (states=%s, submitters=%s, delegates=%s, '
               'archived=%r)' % (','.join(state), ','.join(submitter),
                                 ','.join(delegate), archived))


cli.add_command(apply_cmd)
cli.add_command(show_cmd)
cli.add_command(download_cmd)
cli.add_command(update_cmd)
cli.add_command(list_cmd)

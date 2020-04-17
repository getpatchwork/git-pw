"""
Command-line interface to the Patchwork API.
"""

import click

from git_pw import bundle as bundle_cmds
from git_pw import config
from git_pw import logger
from git_pw import patch as patch_cmds
from git_pw import series as series_cmds

CONF = config.CONF


@click.group()
@click.option('--debug', default=False, is_flag=True,
              help="Output more information about what's going on.")
@click.option('--token', metavar='TOKEN', envvar='PW_TOKEN',
              help="Authentication token. Defaults to the value of "
              "'git config pw.token'.")
@click.option('--username', metavar='USERNAME', envvar='PW_USERNAME',
              help="Authentication username. Defaults to the value of "
              "'git config pw.username'.")
@click.option('--password', metavar='PASSWORD', envvar='PW_PASSWORD',
              help="Authentication password. Defaults to the value of "
              "'git config pw.password'.")
@click.option('--server', metavar='SERVER', envvar='PW_SERVER',
              help="Patchwork server address/hostname. Defaults to the value "
              "of 'git config pw.server'.")
@click.option('--project', metavar='PROJECT', envvar='PW_PROJECT',
              help="Patchwork project. Defaults the value of "
              "'git config pw.project'.")
@click.version_option()
def cli(debug, token, username, password, server, project):
    """git-pw is a tool for integrating Git with Patchwork.

    git-pw can interact with individual patches, complete patch series, and
    customized bundles.  The three major subcommands are *patch*, *bundle*,
    and *series*.

    The git-pw utility is a wrapper which makes REST calls to the Patchwork
    service. To use git-pw, you must set up your environment by configuring
    your Patchwork server URL and either an API token or a username and
    password. To configure the server URL, run::

      git config pw.server http://pw.server.com/path/to/patchwork

    To configure the token, run::

      git config pw.token token

    Alternatively, you can pass these options via command line parameters or
    environment variables.

    For more information on any of the commands, simply pass ``--help`` to the
    appropriate command.
    """
    logger.configure_verbosity(debug)

    CONF.debug = debug
    CONF.token = token
    CONF.username = username
    CONF.password = password
    CONF.server = server
    CONF.project = project


@cli.group()
def patch():
    """Interact with patches.

    Patches are the central object in Patchwork structure. A patch
    contains both a diff and some metadata, such as the name, the
    description, the author, the version of the patch etc. Patchwork
    stores not only the patch itself but also various metadata
    associated with the email that the patch was parsed from, such as
    the message headers or the date the message itself was received.
    """
    pass


@cli.group()
def series():
    """Interact with series.

    Series are groups of patches, along with an optional cover letter.
    Series are mostly dumb containers, though they also contain some
    metadata themselves, such as a version (which is inherited by the
    patches and cover letter) and a count of the number of patches
    found in the series.
    """
    pass


@cli.group()
def bundle():
    """Interact with bundles.

    Bundles are custom, user-defined groups of patches. Bundles can be
    used to keep patch lists, preserving order, for future inclusion in
    a tree. There's no restriction of number of patches and they don't
    even need to be in the same project. A single patch also can be
    part of multiple bundles at the same time.  An example of Bundle
    usage would be keeping track of the Patches that are ready for
    merge to the tree.
    """
    pass


patch.add_command(patch_cmds.apply_cmd)
patch.add_command(patch_cmds.show_cmd)
patch.add_command(patch_cmds.download_cmd)
patch.add_command(patch_cmds.update_cmd)
patch.add_command(patch_cmds.list_cmd)

series.add_command(series_cmds.apply_cmd)
series.add_command(series_cmds.show_cmd)
series.add_command(series_cmds.download_cmd)
series.add_command(series_cmds.list_cmd)

bundle.add_command(bundle_cmds.apply_cmd)
bundle.add_command(bundle_cmds.show_cmd)
bundle.add_command(bundle_cmds.download_cmd)
bundle.add_command(bundle_cmds.list_cmd)
bundle.add_command(bundle_cmds.create_cmd)
bundle.add_command(bundle_cmds.update_cmd)
bundle.add_command(bundle_cmds.delete_cmd)
bundle.add_command(bundle_cmds.add_cmd)
bundle.add_command(bundle_cmds.remove_cmd)

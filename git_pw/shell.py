"""
TODO.
"""

import click

from git_pw import logger
from git_pw import bundle as bundle_cmds
from git_pw import patch as patch_cmds
from git_pw import series as series_cmds


@click.group()
@click.option('--debug', default=False, is_flag=True,
              help="Output more information about what's going on.")
def cli(debug):
    """Interact with a Patchwork instance.

    Patchwork is a patch tracking system for community-based projects.
    It is intended to make the patch management process easier for both
    the project's contributors and maintainers, leaving time for the
    more important (and more interesting) stuff.
    """
    logger.configure_verbosity(debug)


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


@cli.group()
def help():
    """git-pw is a tool for integrating Git with `Patchwork`

    To use git-pw, you must set up your environment by configuring your
    patchwork server url, your username, and your password.  The git-pw
    utility is a wrapper which makes REST calls to the patchwork service.

    Configuring the patchwork url:

      git config pw.server http://pw.server.com/path/to/patchwork

    Configuring username:\n

      git config pw.username userid

    Configuring password:

      git config pw.password pass

    git-pw can interact with individual patches, complete patch series, and
    customized bundles.  The three major subcommands are *patch*, *bundle*,
    and *series*.

    For more information on any of these commands, simply pass --help to the
    appropriate command.
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

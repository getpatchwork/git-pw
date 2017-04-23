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
@click.version_option()
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

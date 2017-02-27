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
    """Interact with Patchwork instance."""
    logger.configure_verbosity(debug)


@cli.group()
def patch():
    """Interact with patches."""
    pass


@cli.group()
def series():
    """Interact with series."""
    pass


@cli.group()
def bundle():
    """Interact with bundles."""
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

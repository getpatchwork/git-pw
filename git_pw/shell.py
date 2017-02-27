"""
TODO.
"""

import click

from git_pw import logger
from git_pw import patch as patch_cmds


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


patch.add_command(patch_cmds.apply_cmd)
patch.add_command(patch_cmds.show_cmd)
patch.add_command(patch_cmds.download_cmd)
patch.add_command(patch_cmds.update_cmd)
patch.add_command(patch_cmds.list_cmd)

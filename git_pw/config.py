"""
Configuration loader using 'git-config'.
"""

import logging

from git_pw import utils

LOG = logging.getLogger(__name__)


def parse_boolean(value: str) -> bool:
    """Parse a boolean config value.

    Based on https://git-scm.com/docs/git-config#_values
    """
    if value in ('yes', 'on', 'true', '1', ''):
        return True

    if value in ('no', 'off', 'false', '0'):
        return False

    LOG.error(f"'{value}' is not a valid boolean value")
    return False


class Config:
    def __init__(self) -> None:
        self._git_config: dict[str, str] = {}

    def __getattribute__(self, name: str) -> str:
        # attempt to use any attributes first
        try:
            value = super().__getattribute__(name)
        except AttributeError:
            value = None
        if value:
            LOG.debug(f"Retrieved '{name}' setting from cache")
            return value

        # fallback to reading from git config otherwise
        value = utils.git_config(f'pw.{name}')
        if value:
            LOG.debug(f"Retrieved '{name}' setting from git-config")

        setattr(self, name, value)

        return value


CONF = Config()

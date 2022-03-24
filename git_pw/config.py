"""
Configuration loader using 'git-config'.
"""

import logging
import typing as ty

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

    LOG.error("'{}' is not a valid boolean value".format(value))
    return False


class Config(object):
    def __init__(self) -> None:
        self._git_config: ty.Dict[str, str] = {}

    def __getattribute__(self, name: str) -> str:
        # attempt to use any attributes first
        try:
            value = super(Config, self).__getattribute__(name)
        except AttributeError:
            value = None
        if value:
            LOG.debug("Retrieved '{}' setting from cache".format(name))
            return value

        # fallback to reading from git config otherwise
        value = utils.git_config('pw.{}'.format(name))
        if value:
            LOG.debug("Retrieved '{}' setting from git-config".format(name))

        setattr(self, name, value)

        return value


CONF = Config()

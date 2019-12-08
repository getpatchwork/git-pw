"""
Configuration loader using 'git-config'.
"""

import logging

from git_pw import utils

LOG = logging.getLogger(__name__)


class Config(object):

    def __init__(self):
        self._git_config = {}

    def __getattribute__(self, name):
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

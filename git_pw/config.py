"""
Configuration loader using 'git-config'.
"""

import logging

from git_pw import utils

LOG = logging.getLogger(__name__)
# TODO(stephenfin): We should eventually download and store these
# automagically
DEFAULT_STATES = [
    'new', 'under-review', 'accepted', 'rejected', 'rfc', 'not-applicable',
    'changes-requested', 'awaiting-upstream', 'superseded', 'deferred']


class Config(object):

    def __init__(self):
        self._git_config = {}

    def __getattribute__(self, name):
        # attempt to use any attributes first
        value = object.__getattribute__(self, name)
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

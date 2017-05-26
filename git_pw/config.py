"""
Configuration loader using 'git-config'.
"""

import logging
import subprocess

LOG = logging.getLogger(__name__)
# TODO(stephenfin): We should eventually download and store these
# automagically
DEFAULT_STATES = [
    'new', 'under-review', 'accepted', 'rejected', 'rfc', 'not-applicable',
    'changes-requested', 'awaiting-upstream', 'superseded', 'deferred']


def _get_config(key):
    """Parse config from 'git-config' cache.

    Returns:
        Matching setting for 'key' if available, else None.
    """
    try:
        output = subprocess.check_output(['git', 'config', 'pw.%s' % key])
    except subprocess.CalledProcessError:
        output = ''

    return output.strip()


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
        value = _get_config(name)
        if value:
            LOG.debug("Retrieved '{}' setting from git-config".format(name))
            value = value.decode('utf-8')

        setattr(self, name, value)

        return value


CONF = Config()

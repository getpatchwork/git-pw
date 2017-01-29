"""
Configuration loader using 'git-config'.
"""

import subprocess

from git_pw import logger

LOG = logger.LOG
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

    output = output.strip()

    LOG.debug('Reading option from git-config: pw.%s=%s', key, output)

    return output


class Config(object):

    def __getattr__(self, name):
        return _get_config(name)


CONF = Config()
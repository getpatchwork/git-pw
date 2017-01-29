"""
Configure application logging.
"""

import logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

LOG = logging.getLogger(__name__)


def configure_verbosity(debug):
    if debug:
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.ERROR)

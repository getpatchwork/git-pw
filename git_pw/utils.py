"""
Utility functions.
"""

import subprocess
import sys


def trim(string, length=70):  # type: (str, int) -> str
    """Trim a string to the given length."""
    return (string[:length - 1] + '...') if len(string) > length else string


def git_am(mbox, args):
    """Execute git-am on a given mbox file."""
    cmd = ['git', 'am']
    if args:
        cmd.extend(args)
    else:
        cmd.append('-3')
    cmd.append(mbox)

    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print(exc.output)
        sys.exit(exc.returncode)

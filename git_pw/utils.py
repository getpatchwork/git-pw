"""
Utility functions.
"""

from __future__ import print_function

import csv
import os
import subprocess
import sys

import click
import six
from tabulate import tabulate


def ensure_str(s):
    if s is None:
        s = ''
    elif not isinstance(s, (six.text_type, six.binary_type)):
        s = str(s)

    return six.ensure_str(s)


def trim(string, length=70):  # type: (str, int) -> str
    """Trim a string to the given length."""
    return (string[:length - 1] + '...') if len(string) > length else string


def git_config(value):
    """Parse config from ``git-config`` cache.

    Returns:
        Matching setting for ``key`` if available, else None.
    """
    try:
        output = subprocess.check_output(['git', 'config', value])
    except subprocess.CalledProcessError:
        output = b''

    return output.decode('utf-8').strip()


def git_am(mbox, args):
    """Execute git-am on a given mbox file."""
    cmd = ['git', 'am']
    if args:
        cmd.extend(args)
    else:
        cmd.append('-3')
    cmd.append(mbox)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print(exc.output.decode('utf-8'))
        sys.exit(exc.returncode)
    else:
        print(output.decode('utf-8'), end='')


def _tabulate(output, headers, fmt):
    fmt = fmt or git_config('pw.format') or 'table'

    if fmt == 'table':
        return tabulate(output, headers, tablefmt='psql')
    elif fmt == 'simple':
        return tabulate(output, headers, tablefmt='simple')
    elif fmt == 'csv':
        result = six.StringIO()
        writer = csv.writer(
            result, quoting=csv.QUOTE_ALL, lineterminator=os.linesep)
        writer.writerow([ensure_str(h) for h in headers])
        for item in output:
            writer.writerow([ensure_str(i) for i in item])
        return result.getvalue()

    print('pw.format must be one of: table, simple, csv')
    sys.exit(1)


def _echo_via_pager(pager, output):
    env = dict(os.environ)
    # When the LESS environment variable is unset, Git sets it to FRX (if
    # LESS environment variable is set, Git does not change it at all).
    if 'LESS' not in env:
        env['LESS'] = 'FRX'

    pager = subprocess.Popen(pager.split(), stdin=subprocess.PIPE, env=env)

    output = six.ensure_binary(output)

    try:
        pager.communicate(input=output)
    except (IOError, KeyboardInterrupt):
        pass
    else:
        pager.stdin.close()

    while True:
        try:
            pager.wait()
        except KeyboardInterrupt:
            pass
        else:
            break


def echo_via_pager(output, headers, fmt):
    """Echo using git's default pager.

    Wrap ``click.echo_via_pager``, setting some environment variables in the
    processs to mimic the pager settings used by Git:

        The order of preference is the ``$GIT_PAGER`` environment variable,
        then ``core.pager`` configuration, then ``$PAGER``, and then the
        default chosen at compile time (usually ``less``).
    """
    output = _tabulate(output, headers, fmt)

    pager = os.environ.get('GIT_PAGER', None)
    if pager:
        _echo_via_pager(pager, output)
        return

    pager = git_config('core.parser')
    if pager:
        _echo_via_pager(pager, output)
        return

    pager = os.environ.get('PAGER', None)
    if pager:
        _echo_via_pager(pager, output)
        return

    _echo_via_pager('less', output)


def echo(output, headers, fmt):
    click.echo(_tabulate(output, headers, fmt))


def pagination_options(sort_fields, default_sort):
    """Shared pagination options."""

    def _pagination_options(f):
        f = click.option('--limit', metavar='LIMIT', type=click.INT,
                         help='Maximum number of items to show.')(f)
        f = click.option('--page', metavar='PAGE', type=click.INT,
                         help='Page to retrieve items from. This is '
                         'influenced by the size of LIMIT.')(f)
        f = click.option('--sort', metavar='FIELD', default=default_sort,
                         type=click.Choice(sort_fields),
                         help='Sort output on given field.')(f)

        return f

    return _pagination_options


def format_options(original_function=None, headers=None):
    """Shared output format options."""

    def _format_options(f):
        f = click.option('--format', '-f', 'fmt', default=None,
                         type=click.Choice(['simple', 'table', 'csv']),
                         help="Output format. Defaults to the value of "
                         "'git config pw.format' else 'table'.")(f)

        if headers:
            f = click.option('--column', '-c', 'headers', metavar='COLUMN',
                             multiple=True, default=headers,
                             type=click.Choice(headers),
                             help='Columns to be included in output.')(f)
        return f

    if original_function:
        return _format_options(original_function)

    return _format_options

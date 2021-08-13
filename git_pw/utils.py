"""
Utility functions.
"""

import csv
import io
import logging
import os
import subprocess
import sys
import typing as ty

import click
from tabulate import tabulate
import yaml

LOG = logging.getLogger(__name__)


def ensure_str(s: ty.Any) -> str:
    if s is None:
        s = ''
    elif isinstance(s, bytes):
        s = s.decode('utf-8', 'strict')
    elif not isinstance(s, str):
        s = str(s)

    return s


def trim(string: str, length: int = 70) -> str:
    """Trim a string to the given length."""
    return (string[: length - 1] + '...') if len(string) > length else string


def git_config(value: str) -> str:
    """Parse config from ``git-config`` cache.

    Returns:
        Matching setting for ``key`` if available, else None.
    """
    cmd = ['git', 'config', value]

    LOG.debug('Fetching git config info for %s', value)
    LOG.debug('Running: %s', ' '.join(cmd))

    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        output = b''

    return output.decode('utf-8').strip()


def git_am(mbox: str, args: ty.Tuple[str, ...]) -> None:
    """Execute git-am on a given mbox file."""
    cmd = ['git', 'am']
    if args:
        cmd.extend(args)
    else:
        cmd.append('-3')
    cmd.append(mbox)

    LOG.debug('Applying patch at %s', mbox)
    LOG.debug('Running: %s', ' '.join(cmd))

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        LOG.error('Failed to apply patch:\n%s', exc.output.decode('utf-8'))
        sys.exit(exc.returncode)
    else:
        LOG.info(output.decode('utf-8'))


def _tabulate(
    output: ty.List[ty.Tuple[str, ty.Any]],
    headers: ty.List[str],
    fmt: str,
) -> str:
    fmt = fmt or git_config('pw.format') or 'table'

    if fmt == 'table':
        return tabulate(output, headers, tablefmt='psql')
    elif fmt == 'simple':
        return tabulate(output, headers, tablefmt='simple')
    elif fmt == 'csv':
        result = io.StringIO()
        writer = csv.writer(
            result, quoting=csv.QUOTE_ALL, lineterminator=os.linesep
        )
        writer.writerow([ensure_str(h) for h in headers])
        for item in output:
            writer.writerow([ensure_str(i) for i in item])
        return result.getvalue()
    elif fmt == 'yaml':
        data = [
            {headers[i].lower(): entry[i] for i in range(len(headers))}
            for entry in output
        ]
        return yaml.dump(data, default_flow_style=False)

    LOG.error('pw.format must be one of: table, simple, csv, yaml')
    sys.exit(1)


def _echo_via_pager(pager: str, output: str) -> None:
    env = dict(os.environ)
    # When the LESS environment variable is unset, Git sets it to FRX (if
    # LESS environment variable is set, Git does not change it at all).
    if 'LESS' not in env:
        env['LESS'] = 'FRX'

    proc = subprocess.Popen(pager.split(), stdin=subprocess.PIPE, env=env)

    try:
        proc.communicate(input=output.encode('utf-8', 'strict'))
    except (IOError, KeyboardInterrupt):
        pass
    else:
        if proc.stdin:
            proc.stdin.close()

    while True:
        try:
            proc.wait()
        except KeyboardInterrupt:
            pass
        else:
            break


def echo_via_pager(
    output: ty.List[ty.Tuple[str, ty.Any]],
    headers: ty.List[str],
    fmt: str,
) -> None:
    """Echo using git's default pager.

    Wrap ``click.echo_via_pager``, setting some environment variables in the
    processs to mimic the pager settings used by Git:

        The order of preference is the ``$GIT_PAGER`` environment variable,
        then ``core.pager`` configuration, then ``$PAGER``, and then the
        default chosen at compile time (usually ``less``).
    """
    out = _tabulate(output, headers, fmt)

    pager = os.environ.get('GIT_PAGER', None)
    if pager:
        _echo_via_pager(pager, out)
        return

    pager = git_config('core.parser')
    if pager:
        _echo_via_pager(pager, out)
        return

    pager = os.environ.get('PAGER', None)
    if pager:
        _echo_via_pager(pager, out)
        return

    _echo_via_pager('less', out)


def echo(
    output: ty.List[ty.Tuple[str, ty.Any]],
    headers: ty.List[str],
    fmt: str,
) -> None:
    click.echo(_tabulate(output, headers, fmt))


def pagination_options(
    sort_fields: ty.Tuple[str, ...],
    default_sort: str,
) -> ty.Callable:
    """Shared pagination options."""

    def _pagination_options(f):
        f = click.option(
            '--limit',
            metavar='LIMIT',
            type=click.INT,
            help='Maximum number of items to show.',
        )(f)
        f = click.option(
            '--page',
            metavar='PAGE',
            type=click.INT,
            help='Page to retrieve items from. This is '
            'influenced by the size of LIMIT.',
        )(f)
        f = click.option(
            '--sort',
            metavar='FIELD',
            default=default_sort,
            type=click.Choice(sort_fields),
            help='Sort output on given field.',
        )(f)

        return f

    return _pagination_options


def format_options(
    original_function: ty.Callable = None,
    headers: ty.Tuple[str, ...] = None,
) -> ty.Callable:
    """Shared output format options."""

    def _format_options(f):
        f = click.option(
            '--format',
            '-f',
            'fmt',
            default=None,
            type=click.Choice(['simple', 'table', 'csv', 'yaml']),
            help=(
                "Output format. Defaults to the value of "
                "'git config pw.format' else 'table'."
            ),
        )(f)

        if headers:
            f = click.option(
                '--column',
                '-c',
                'headers',
                metavar='COLUMN',
                multiple=True,
                default=headers,
                type=click.Choice(headers),
                help='Columns to be included in output.',
            )(f)
        return f

    if original_function:
        return _format_options(original_function)

    return _format_options

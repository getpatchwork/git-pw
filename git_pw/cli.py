#!/usr/bin/env python

"""
git-pw: TODO
"""

from __future__ import print_function

import argparse
import os
import subprocess
import sys
import xml

if sys.version < '3':
    import xmlrpclib
else:
    import xmlrpc.client as xmlrpclib

import pkg_resources


def get_version():
    try:
        return pkg_resources.get_provider(
            pkg_resources.Requirement.parse('git-pw'))
    except pkg_resources.DistributionNotFound:
        return 0


class GitPWException(Exception):
    msg_fmt = 'An unknown exception occured'

    def __init__(self, message=None, **kwargs):
        if not message:
            try:
                message = self.msg_fmt % kwargs
            except KeyError:
                # someone did something silly, but print the message anyway
                message = self.msg_fmt

        self.message = message
        super(GitPWException, self).__init__(message)


class ConnectionFailed(GitPWException):
    msg_fmt = 'Unable to connect to \'%(host)s\': %(reason)s'


class UnsupportedOperation(GitPWException):
    msg_fmt = ('Your patchwork version is too old. '
               'Expected: %(expected)s, Actual: %(actual)s')


class InvalidPatchID(GitPWException):
    msg_fmt = 'The patch \'%(patch_id)s\' was not found'


class MissingConfig(GitPWException):
    msg_fmt = 'The key \'%(name)s\' was not found. Did you set it?'


def _get_connection(host=None):
    """Creates an connection to the XML-RPC API."""
    if not host:
        host = get_config('pw.server')

    try:
        api = xmlrpclib.ServerProxy(host)
        api.pw_rpc_version()  # ensure the connection is actually valid
    except xmlrpclib.ProtocolError:
        raise ConnectionFailed(host=host, reason='protocol error')
    except xml.parsers.expat.ExpatError:
        raise ConnectionFailed(host=host, reason='invalid response')
    except Exception:
        raise ConnectionFailed(host=host, reason='unknown error')

    return api


def _run_command(args, stdin=None):
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE if stdin else None)
    (out, _) = p.communicate(stdin)
    out = out.decode('utf-8', 'replace').strip()

    return (p.returncode, out)


def require_api_version(version):
    """Ensure PW API is correct version for command.

    This allows the application to gracefully degrade, based on the features
    of the API.
    """
    def _require_api_version_inner(func):
        def _validation_wrapper(*args, **kwargs):
            api = _get_connection()
            pw_version = api.pw_rpc_version()

            # NOTE(stephenfin): Older versions of the API return an int, hence
            # need to cast
            if pw_version == 1:
                pw_version = (1, 0, 0)

            if pw_version < version:
                raise UnsupportedOperation(expected=version, actual=pw_version)

            func(*args, **kwargs)

        return _validation_wrapper

    return _require_api_version_inner


def get_config(name, default=None):
    cmd = ['git', 'config', '--get', name]
    code, output = _run_command(cmd)

    # TODO(stephenfin): Handle non-'1' return codes:
    #   https://www.kernel.org/pub/software/scm/git/docs/git-config.html
    if code:
        if default:
            return default
        raise MissingConfig(name=name)

    return output


def cherrypick_patch(patch_id):
    # TODO(stephenfin): Document this variable
    api = _get_connection()
    patch = api.patch_get_mbox(patch_id)
    if not patch:
        raise InvalidPatchID(patch_id=patch_id)

    # TODO(stephenfin): We should probably make sure the patch applies
    # cleanly before doing so. Maybe '--dry-run'?
    cmd = ['git', 'am']
    code, output = _run_command(cmd, patch)
    # TODO(stephenfin): Use an exception here
    if code:
        print(output)
        sys.exit(1)


# TODO(stephenfin): Series support has still not merged so this version should
# be updated when appropriate
@require_api_version((1, 1, 0))
def download_patch(patch_id):
    raise NotImplementedError('Series support is still in limbo')


# TODO(stephenfin): Series support has still not merged so this version should
# be updated when appropriate
@require_api_version((1, 1, 0))
def download_series(series_id):
    raise NotImplementedError('Series support is still in limbo')


def list_patches():
    # TODO(stephenfin): Document this variable
    api = _get_connection()

    # TODO(stephenfin): Limit patches to open status
    # TODO(stephenfin): Document this variable
    patches = api.patch_list({'project_id': get_config('pw.projectid')})
    patches = [(patch['id'], patch['project'], patch['name']) for patch in patches]

    for patch in patches:
        # TODO(stephenfin): It would be good to calculate the length of these
        # fields dynamically
        # TODO(stephenfin): Colour is good. We should use some.
        print('%6s  %12s  %s' % patch)


def main():
    usage = 'git pw [OPTIONS...] [BRANCH]'

    class DownloadAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)
            setattr(namespace, self.const, True)

    parser = argparse.ArgumentParser(usage=usage, description=__doc__)

    # Patch/series download arguments
    download = parser.add_mutually_exclusive_group()
    download.set_defaults(download=False, series=False, ancestry=False)
    download.add_argument('-x', '--cherrypick',
                          metavar='PATCH_ID',
                          action=DownloadAction,
                          const='cherrypick',
                          dest='patch_id',
                          help='download a patch by itself and apply to the '
                               'specified branch. This is somewhat analogous '
                               'to the cherry-pick command in Git')
    download.add_argument('-d', '--download',
                          metavar='PATCH_ID',
                          action=DownloadAction,
                          const='download',
                          dest='patch_id',
                          help='download a patch and all its ancestors, if '
                               'any, and apply to the specified branch ')
    download.add_argument('-s', '--series',
                          metavar='SERIES_ID',
                          action=DownloadAction,
                          const='series',
                          dest='series_id',
                          help='download an entire series and apply to the '
                               'specified branch')

    # Additional arguments
    parser.set_defaults(branch='HEAD',
                        list=False)
    parser.add_argument('branch',
                        nargs='?',
                        help='the branch to apply any downloaded patch(es) to')
    parser.add_argument('-l', '--list',
                        action='store_true',
                        dest='list',
                        help='list available reviews for the current project')

    # Helper arguments
    parser.set_defaults(verbose=False,
                        list=False)
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        dest='verbose',
                        help='enable verbose logging to the screen')
    parser.add_argument('--version',
                        action='version',
                        version='%s version %s' %
                        (os.path.split(sys.argv[0])[-1], get_version()))

    options = parser.parse_args()

    if options.list:
        list_patches()
        return

    if options.patch_id:
        if options.download:
            download_patch(options.patch_id)
        else:
            cherrypick_patch(options.patch_id)
        return

    if options.series_id:
        download_series(options.series_id)
        return


if __name__ == '__main__':
    main()

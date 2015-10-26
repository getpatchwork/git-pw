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


class InvalidPatchID(GitPWException):
    msg_fmt = 'The patch \'%(patch_id)s\' was not found'


def _get_connection(host):
    """Creates an connection to the XML-RPC API."""
    try:
        api = xmlrpclib.ServerProxy(host)
        version = api.pw_rpc_version()
    except xmlrpclib.ProtocolError:
        raise ConnectionFailed(host=host, reason='protocol error')
    except xml.parsers.expat.ExpatError:
        raise ConnectionFailed(host=host, reason='invalid response')
    except Exception:
        raise ConnectionFailed(host=host, reason='unknown error')

    # NOTE(stephenfin): Older versions of the API return an int, hence
    # need to cast
    version = version if type(version) is tuple else (version, )
    if version < (1, 1, 0):
        # TODO(stephenfin): Some graceful degradation would be nice
        # TODO(stephenfin): Use an exception here
        print('Your version of patchwork is too old. Please upgrade it.')
        sys.exit(1)

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


def cherrypick_patch(patch_id):
    # TODO(stephenfin): Parse hostnames from...somewhere...
    api = _get_connection('http://patchwork.ozlabs.org/xmlrpc/')
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


def download_patch(patch_id):
    raise NotImplementedError('Series support is still in limbo')


def download_series(series_id):
    raise NotImplementedError('Series support is still in limbo')


def list_patches():
    pass


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

#!/usr/bin/env python

"""
git-pw: TODO
"""

from __future__ import print_function

import argparse
import os
import sys


import pkg_resources


def get_version():
    try:
        return pkg_resources.get_provider(
            pkg_resources.Requirement.parse('git-pw'))
    except pkg_resources.DistributionNotFound:
        return 0


def cherrypick_patch(patch_id):
    pass


def download_patch(patch_id):
    pass


def download_series(series_id):
    pass


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

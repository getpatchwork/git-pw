# -*- coding: utf-8 -*-

"""Unit tests for ``git_pw/utils.py``."""

import subprocess
import textwrap
import os

import yaml
from unittest import mock

from git_pw import utils


@mock.patch.object(utils.subprocess, 'check_output', return_value=b' bar ')
def test_git_config(mock_subprocess):
    value = utils.git_config('foo')

    assert value == 'bar'
    mock_subprocess.assert_called_once_with(['git', 'config', 'foo'])


@mock.patch.object(utils.subprocess, 'check_output',
                   return_value=b'\xf0\x9f\xa4\xb7')
def test_git_config_unicode(mock_subprocess):
    value = utils.git_config('foo')

    assert value == u'\U0001f937'
    mock_subprocess.assert_called_once_with(['git', 'config', 'foo'])


@mock.patch.object(utils.subprocess, 'check_output',
                   side_effect=subprocess.CalledProcessError(1, 'xyz', '123'))
def test_git_config_error(mock_subprocess):
    value = utils.git_config('foo')

    assert value == ''


@mock.patch.object(utils, 'git_config', return_value='bar')
@mock.patch.object(utils, '_tabulate')
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'GIT_PAGER': 'foo', 'PAGER': 'baz'})
def test_echo_via_pager_env_GIT_PAGER(mock_inner, mock_tabulate, mock_config):
    utils.echo_via_pager('test', ('foo',), None)

    mock_config.assert_not_called()
    mock_tabulate.assert_called_once_with('test', ('foo',), None)
    mock_inner.assert_called_once_with('foo', mock_tabulate.return_value)


@mock.patch.object(utils, 'git_config', return_value='bar')
@mock.patch.object(utils, '_tabulate')
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'PAGER': 'baz'})
def test_echo_via_pager_config(mock_inner, mock_tabulate, mock_config):
    utils.echo_via_pager('test', ('foo',), None)

    mock_config.assert_called_once_with('core.parser')
    mock_tabulate.assert_called_once_with('test', ('foo',), None)
    mock_inner.assert_called_once_with('bar', mock_tabulate.return_value)


@mock.patch.object(utils, 'git_config', return_value=None)
@mock.patch.object(utils, '_tabulate')
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'PAGER': 'baz'})
def test_echo_via_pager_env_PAGER(mock_inner, mock_tabulate, mock_config):
    utils.echo_via_pager('test', ('foo',), None)

    mock_config.assert_called_once_with('core.parser')
    mock_tabulate.assert_called_once_with('test', ('foo',), None)
    mock_inner.assert_called_once_with('baz', mock_tabulate.return_value)


@mock.patch.object(utils, 'git_config', return_value=None)
@mock.patch.object(utils, '_tabulate')
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'PAGER': ''})
def test_echo_via_pager_env_default(mock_inner, mock_tabulate, mock_config):
    utils.echo_via_pager('test', ('foo',), None)

    mock_config.assert_called_once_with('core.parser')
    mock_tabulate.assert_called_once_with('test', ('foo',), None)
    mock_inner.assert_called_once_with('less', mock_tabulate.return_value)


def _test_tabulate(fmt):
    output = [(b'foo', 'bar', u'baz', '😀', None, 1)]
    headers = ('col1', 'colb', 'colIII', 'colX', 'colY', 'colZ')

    result = utils._tabulate(output, headers, fmt)

    return output, headers, result


@mock.patch.object(utils, 'tabulate')
def test_tabulate_table(mock_tabulate):
    output, headers, result = _test_tabulate('table')

    mock_tabulate.assert_called_once_with(output, headers, tablefmt='psql')
    assert result == mock_tabulate.return_value


@mock.patch.object(utils, 'tabulate')
def test_tabulate_simple(mock_tabulate):
    output, headers, result = _test_tabulate('simple')

    mock_tabulate.assert_called_once_with(output, headers, tablefmt='simple')
    assert result == mock_tabulate.return_value


@mock.patch.object(utils, 'tabulate')
def test_tabulate_csv(mock_tabulate):
    output, headers, result = _test_tabulate('csv')

    mock_tabulate.assert_not_called()
    assert result == textwrap.dedent("""\
        "col1","colb","colIII","colX","colY","colZ"
        "foo","bar","baz","😀","","1"
    """)


@mock.patch.object(yaml, 'dump')
def test_tabulate_yaml(mock_dump):
    output, headers, result = _test_tabulate('yaml')

    mock_dump.assert_called_once_with(
        [{
            'col1': b'foo',
            'colb': 'bar',
            'coliii': u'baz',
            'colx': '😀',
            'coly': None,
            'colz': 1,
        }],
        default_flow_style=False,
    )


@mock.patch.object(utils, 'git_config', return_value='simple')
@mock.patch.object(utils, 'tabulate')
def test_tabulate_git_config(mock_tabulate, mock_git_config):
    output, headers, result = _test_tabulate(None)

    mock_git_config.assert_called_once_with('pw.format')
    mock_tabulate.assert_called_once_with(output, headers, tablefmt='simple')
    assert result == mock_tabulate.return_value


@mock.patch.object(utils, 'git_config', return_value='')
@mock.patch.object(utils, 'tabulate')
def test_tabulate_default(mock_tabulate, mock_git_config):
    output, headers, result = _test_tabulate(None)

    mock_git_config.assert_called_once_with('pw.format')
    mock_tabulate.assert_called_once_with(output, headers, tablefmt='psql')
    assert result == mock_tabulate.return_value

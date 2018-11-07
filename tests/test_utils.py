"""Unit tests for ``git_pw/utils.py``."""

import subprocess
import os

import mock

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
def test_echo_via_pager_env_default(mock_inner, mock_tabulate, mock_config):
    utils.echo_via_pager('test', ('foo',), None)

    mock_config.assert_called_once_with('core.parser')
    mock_tabulate.assert_called_once_with('test', ('foo',), None)
    mock_inner.assert_called_once_with('less', mock_tabulate.return_value)

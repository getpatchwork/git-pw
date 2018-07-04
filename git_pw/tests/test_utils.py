"""Unit tests for ``git_pw/utils.py``."""

import os

import mock

from git_pw import utils


@mock.patch.object(utils, 'git_config', return_value='bar')
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'GIT_PAGER': 'foo', 'PAGER': 'baz'})
def test_echo_via_pager_env_GIT_PAGER(mock_inner, mock_config):
    utils.echo_via_pager('test')

    mock_config.assert_not_called()
    mock_inner.assert_called_once_with('foo', 'test')


@mock.patch.object(utils, 'git_config', return_value='bar')
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'PAGER': 'baz'})
def test_echo_via_pager_config(mock_inner, mock_config):
    utils.echo_via_pager('test')

    mock_config.assert_called_once_with('core.parser')
    mock_inner.assert_called_once_with('bar', 'test')


@mock.patch.object(utils, 'git_config', return_value=None)
@mock.patch.object(utils, '_echo_via_pager')
@mock.patch.dict(os.environ, {'PAGER': 'baz'})
def test_echo_via_pager_env_PAGER(mock_inner, mock_config):
    utils.echo_via_pager('test')

    mock_config.assert_called_once_with('core.parser')
    mock_inner.assert_called_once_with('baz', 'test')

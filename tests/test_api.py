"""Unit tests for ``git_pw/api.py``."""

from unittest import mock

import requests
import pytest

from git_pw import api


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'CONF')
def test_get_server_undefined(mock_conf, mock_log):
    mock_conf.server = None

    with pytest.raises(SystemExit):
        api._get_server()

    assert mock_log.error.called


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'CONF')
def test_get_server_missing_version(mock_conf, mock_log):
    mock_conf.server = 'https://example.com/api'

    server = api._get_server()

    assert mock_log.warning.called
    assert server == 'https://example.com/api'


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'CONF')
def test_get_server_missing_version_and_path(mock_conf, mock_log):
    mock_conf.server = 'https://example.com/'

    server = api._get_server()

    assert mock_log.warning.called
    assert server == 'https://example.com/api'


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'CONF')
def test_get_project_undefined(mock_conf, mock_log):
    mock_conf.project = None

    with pytest.raises(SystemExit):
        api._get_project()

    assert mock_log.error.called


@mock.patch.object(api, 'CONF')
def test_get_project_wildcard(mock_conf):
    mock_conf.project = '*'

    project = api._get_project()

    assert project == ''


@mock.patch.object(api, '_get_server')
def test_version_missing(mock_server):
    mock_server.return_value = 'https://example.com/api'

    assert api.version() == (1, 0)


@mock.patch.object(api, '_get_server')
def test_version(mock_server):
    mock_server.return_value = 'https://example.com/api/1.1'

    assert api.version() == (1, 1)


def test_handle_error__server_error(caplog):
    fake_response = mock.MagicMock(autospec=requests.Response)
    fake_response.content = b'InternalServerError'
    fake_response.status_code = 500
    exc = requests.exceptions.RequestException(response=fake_response)

    with pytest.raises(SystemExit):
        api._handle_error('fetch', exc)

    assert 'Server error.' in caplog.text


def test_handle_error__not_found(caplog):
    fake_response = mock.MagicMock(autospec=requests.Response)
    fake_response.content = b'NotFound'
    fake_response.status_code = 404
    exc = requests.exceptions.RequestException(response=fake_response)

    with pytest.raises(SystemExit):
        api._handle_error('fetch', exc)

    assert 'Resource not found' in caplog.text


def test_handle_error__other(caplog):
    fake_response = mock.MagicMock(autospec=requests.Response)
    fake_response.content = b'{"key": "value"}'
    fake_response.status_code = 403
    fake_response.text = '{"key": "value"}'
    exc = requests.exceptions.RequestException(response=fake_response)

    with pytest.raises(SystemExit):
        api._handle_error('fetch', exc)

    assert '{"key": "value"}' in caplog.text


def test_handle_error__no_response(caplog):
    exc = requests.exceptions.RequestException()

    with pytest.raises(SystemExit):
        api._handle_error('fetch', exc)

    assert 'Failed to fetch resource.' in caplog.text


@mock.patch.object(api, 'index')
def test_retrieve_filter_ids_too_short(mock_index):
    with pytest.raises(SystemExit):
        api.retrieve_filter_ids('users', 'owner', 'f')

    assert not mock_index.called


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'index')
def test_retrieve_filter_ids_no_matches(mock_index, mock_log):
    mock_index.return_value = []

    ids = api.retrieve_filter_ids('users', 'owner', 'foo')

    assert mock_log.warning.called
    assert ids == []


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'version')
@mock.patch.object(api, 'index')
def test_retrieve_filter_ids_multiple_matches_1_0(
    mock_index, mock_version, mock_log
):
    mock_index.return_value = [
        {'id': 1},
        {'id': 2},  # incomplete but good enough
    ]
    mock_version.return_value = (1, 0)

    ids = api.retrieve_filter_ids('users', 'owner', 'foo')

    assert mock_log.warning.called
    assert ids == [('owner', 1), ('owner', 2)]


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'version')
@mock.patch.object(api, 'index')
def test_retrieve_filter_ids_multiple_matches_1_1(
    mock_index, mock_version, mock_log
):
    mock_index.return_value = [
        {'id': 1},
        {'id': 2},  # incomplete but good enough
    ]
    mock_version.return_value = (1, 1)

    ids = api.retrieve_filter_ids('users', 'owner', 'foo')

    assert not mock_log.warning.called
    assert ids == [('owner', 1), ('owner', 2)]


@mock.patch.object(api, 'LOG')
@mock.patch.object(api, 'index')
def test_retrieve_filter_ids(mock_index, mock_log):
    mock_index.return_value = [{'id': 1}]

    ids = api.retrieve_filter_ids('users', 'owner', 'foo')

    assert not mock_log.warning.called
    assert ids == [('owner', 1)]

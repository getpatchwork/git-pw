import unittest
from unittest import mock

from click.testing import CliRunner as CLIRunner

from git_pw import series


@mock.patch('git_pw.api.detail')
@mock.patch('git_pw.api.download')
@mock.patch('git_pw.utils.git_am')
class ApplyTestCase(unittest.TestCase):

    def test_apply_without_args(self, mock_git_am, mock_download, mock_detail):
        """Validate calling with no arguments."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_detail.return_value = rsp
        mock_download.return_value = 'test.patch'

        runner = CLIRunner()
        result = runner.invoke(series.apply_cmd, ['123'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('series', 123)
        mock_download.assert_called_once_with(rsp['mbox'])
        mock_git_am.assert_called_once_with(mock_download.return_value, ())

    def test_apply_with_args(self, mock_git_am, mock_download, mock_detail):
        """Validate passthrough of arbitrary arguments to git-am."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_detail.return_value = rsp
        mock_download.return_value = 'test.patch'

        runner = CLIRunner()
        result = runner.invoke(series.apply_cmd, ['123', '-3'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('series', 123)
        mock_download.assert_called_once_with(rsp['mbox'])
        mock_git_am.assert_called_once_with(mock_download.return_value,
                                            ('-3',))


@mock.patch('git_pw.api.detail')
@mock.patch('git_pw.api.download')
class DownloadTestCase(unittest.TestCase):

    def test_download(self, mock_download, mock_detail):
        """Validate standard behavior."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_detail.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(series.download_cmd, ['123'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('series', 123)
        mock_download.assert_called_once_with(rsp['mbox'], output=None)

    def test_download_to_file(self, mock_download, mock_detail):
        """Validate downloading to a file."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_detail.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(series.download_cmd, ['123', 'test.patch'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('series', 123)
        mock_download.assert_called_once_with(rsp['mbox'], output=mock.ANY)
        assert isinstance(
            mock_download.call_args[1]['output'], str,
        )

    def test_download_separate_to_dir(self, mock_download, mock_detail):
        """Validate downloading seperate to a directory."""

        rsp = {
            'mbox': 'http://example.com/api/patches/123/mbox/',
            'patches': [
                {
                    'id': 10539359,
                    'mbox': 'https://example.com/project/foo/patch/123/mbox/',
                }

            ]
        }
        mock_detail.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(series.download_cmd, ['123', '--separate', '.'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('series', 123)
        mock_download.assert_called_once_with(
            rsp['patches'][0]['mbox'], output=mock.ANY,
        )
        assert isinstance(
            mock_download.call_args[1]['output'], str,
        )


class ShowTestCase(unittest.TestCase):

    @staticmethod
    def _get_series(**kwargs):
        rsp = {
            'id': 123,
            'date': '2017-01-01 00:00:00',
            'name': 'Sample series',
            'submitter': {
                'name': 'foo',
                'email': 'foo@bar.com',
            },
            'project': {
                'name': 'bar',
            },
            'version': '1',
            'total': 2,
            'received_total': 2,
            'received_all': True,
            'cover_letter': None,
            'patches': [],
        }

        rsp.update(**kwargs)

        return rsp

    @mock.patch('git_pw.api.detail')
    def test_show(self, mock_detail):
        """Validate standard behavior."""

        rsp = self._get_series()
        mock_detail.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(series.show_cmd, ['123'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('series', 123)


@mock.patch('git_pw.api.version', return_value=(1, 0))
@mock.patch('git_pw.api.index')
@mock.patch('git_pw.utils.echo_via_pager')
class ListTestCase(unittest.TestCase):

    @staticmethod
    def _get_series(**kwargs):
        return ShowTestCase._get_series(**kwargs)

    @staticmethod
    def _get_people(**kwargs):
        rsp = {
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
        }
        rsp.update(**kwargs)
        return rsp

    def test_list(self, mock_echo, mock_index, mock_version):
        """Validate standard behavior."""

        rsp = [self._get_series()]
        mock_index.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(series.list_cmd, [])

        assert result.exit_code == 0, result
        mock_index.assert_called_once_with('series', [
            ('q', None), ('page', None), ('per_page', None),
            ('order', '-date')])

    def test_list_with_formatting(self, mock_echo, mock_index, mock_version):
        """Validate behavior with formatting applied."""

        rsp = [self._get_series()]
        mock_index.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(series.list_cmd, [
            '--format', 'simple', '--column', 'ID', '--column', 'Name'])

        assert result.exit_code == 0, result

        mock_echo.assert_called_once_with(mock.ANY, ('ID', 'Name'),
                                          fmt='simple')

    def test_list_with_filters(self, mock_echo, mock_index, mock_version):
        """Validate behavior with filters applied.

        Apply all filters, including those for pagination.
        """

        people_rsp = [self._get_people()]
        series_rsp = [self._get_series()]
        mock_index.side_effect = [people_rsp, series_rsp]

        runner = CLIRunner()
        result = runner.invoke(series.list_cmd, [
            '--submitter', 'john@example.com', '--submitter', '2',
            '--limit', 1, '--page', 1, '--sort', '-name', 'test'])

        assert result.exit_code == 0, result
        calls = [
            mock.call('people', [('q', 'john@example.com')]),
            mock.call('series', [
                ('submitter', 1), ('submitter', '2'), ('q', 'test'),
                ('page', 1), ('per_page', 1), ('order', '-name')])]

        mock_index.assert_has_calls(calls)

    @mock.patch('git_pw.api.LOG')
    def test_list_with_wildcard_filters(self, mock_log, mock_echo, mock_index,
                                        mock_version):
        """Validate behavior with a "wildcard" filter.

        Patchwork API v1.0 did not support multiple filters correctly. Ensure
        the user is warned as necessary if a filter has multiple matches.
        """

        people_rsp = [self._get_people(), self._get_people()]
        series_rsp = [self._get_series()]
        mock_index.side_effect = [people_rsp, series_rsp]

        runner = CLIRunner()
        runner.invoke(series.list_cmd, ['--submitter', 'john@example.com'])

        assert mock_log.warning.called

    @mock.patch('git_pw.api.LOG')
    def test_list_with_multiple_filters(self, mock_log, mock_echo, mock_index,
                                        mock_version):
        """Validate behavior with use of multiple filters.

        Patchwork API v1.0 did not support multiple filters correctly. Ensure
        the user is warned as necessary if they specify multiple filters.
        """

        people_rsp = [self._get_people()]
        series_rsp = [self._get_series()]
        mock_index.side_effect = [people_rsp, people_rsp, series_rsp]

        runner = CLIRunner()
        result = runner.invoke(series.list_cmd, [
            '--submitter', 'john@example.com',
            '--submitter', 'jimmy@example.com'])

        assert result.exit_code == 0, result
        assert mock_log.warning.called

    @mock.patch('git_pw.api.LOG')
    def test_list_api_v1_1(self, mock_log, mock_echo, mock_index,
                           mock_version):
        """Validate behavior with API v1.1."""

        mock_version.return_value = (1, 1)

        people_rsp = [self._get_people()]
        series_rsp = [self._get_series()]
        mock_index.side_effect = [people_rsp, series_rsp]

        runner = CLIRunner()
        result = runner.invoke(series.list_cmd, [
            '--submitter', 'jimmy@example.com',
            '--submitter', 'John Doe'])

        assert result.exit_code == 0, result

        # We should have only made a single call to '/people' since API v1.1
        # supports filtering with emails natively
        calls = [
            mock.call('people', [('q', 'John Doe')]),
            mock.call('series', [
                ('submitter', 'jimmy@example.com'), ('submitter', 1),
                ('q', None), ('page', None), ('per_page', None),
                ('order', '-date')])]
        mock_index.assert_has_calls(calls)

        # We shouldn't see a warning about multiple versions either
        assert not mock_log.warning.called

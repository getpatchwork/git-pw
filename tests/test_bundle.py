import unittest
from unittest import mock

from click.testing import CliRunner as CLIRunner

from git_pw import bundle


@mock.patch('git_pw.api.detail')
@mock.patch('git_pw.api.index')
class GetBundleTestCase(unittest.TestCase):
    """Test the ``_get_bundle`` function."""

    def test_get_by_id(self, mock_index, mock_detail):
        """Validate using a number (bundle ID)."""

        # not a valid return value (should be a JSON response) but good enough
        mock_detail.return_value = 'hello, world'

        result = bundle._get_bundle('123')

        assert result == mock_detail.return_value, result
        mock_index.assert_not_called()
        mock_detail.assert_called_once_with('bundles', '123')

    def test_get_by_name(self, mock_index, mock_detail):
        """Validate using a string (bundle name)."""

        # not a valid return value (should be a JSON response) but good enough
        mock_index.return_value = ['hello, world']

        result = bundle._get_bundle('test')

        assert result == mock_index.return_value[0], result
        mock_detail.assert_not_called()
        mock_index.assert_called_once_with('bundles', [('q', 'test')])

    def test_get_by_name_too_many_matches(self, mock_index, mock_detail):
        """Validate using a string that returns too many results."""

        # not valid return values (should be a JSON response) but good enough
        mock_index.return_value = ['hello, world', 'uh oh']

        with self.assertRaises(SystemExit):
            bundle._get_bundle('test')

    def test_get_by_name_too_few_matches(self, mock_index, mock_detail):
        """Validate using a string that returns too few (no) results."""

        mock_index.return_value = []

        with self.assertRaises(SystemExit):
            bundle._get_bundle('test')


@mock.patch('git_pw.bundle._get_bundle')
@mock.patch('git_pw.api.download')
@mock.patch('git_pw.utils.git_am')
class ApplyTestCase(unittest.TestCase):

    def test_apply_without_args(self, mock_git_am, mock_download,
                                mock_get_bundle):
        """Validate calling with no arguments."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_get_bundle.return_value = rsp
        mock_download.return_value = 'test.patch'

        runner = CLIRunner()
        result = runner.invoke(bundle.apply_cmd, ['123'])

        assert result.exit_code == 0, result
        mock_get_bundle.assert_called_once_with('123')
        mock_download.assert_called_once_with(rsp['mbox'])
        mock_git_am.assert_called_once_with(mock_download.return_value, ())

    def test_apply_with_args(self, mock_git_am, mock_download,
                             mock_get_bundle):
        """Validate passthrough of arbitrary arguments to git-am."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_get_bundle.return_value = rsp
        mock_download.return_value = 'test.patch'

        runner = CLIRunner()
        result = runner.invoke(bundle.apply_cmd, ['123', '-3'])

        assert result.exit_code == 0, result
        mock_get_bundle.assert_called_once_with('123')
        mock_download.assert_called_once_with(rsp['mbox'])
        mock_git_am.assert_called_once_with(mock_download.return_value,
                                            ('-3',))


@mock.patch('git_pw.bundle._get_bundle')
@mock.patch('git_pw.api.download')
class DownloadTestCase(unittest.TestCase):

    def test_download(self, mock_download, mock_get_bundle):
        """Validate standard behavior."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_get_bundle.return_value = rsp
        mock_download.return_value = 'test.patch'

        runner = CLIRunner()
        result = runner.invoke(bundle.download_cmd, ['123'])

        assert result.exit_code == 0, result
        mock_get_bundle.assert_called_once_with('123')
        mock_download.assert_called_once_with(rsp['mbox'], output=None)

    def test_download_to_file(self, mock_download, mock_get_bundle):
        """Validate downloading to a file."""

        rsp = {'mbox': 'http://example.com/api/patches/123/mbox/'}
        mock_get_bundle.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(bundle.download_cmd, ['123', 'test.patch'])

        assert result.exit_code == 0, result

        mock_get_bundle.assert_called_once_with('123')
        mock_download.assert_called_once_with(rsp['mbox'], output=mock.ANY)
        assert isinstance(
            mock_download.call_args[1]['output'], str,
        )


class ShowTestCase(unittest.TestCase):

    @staticmethod
    def _get_bundle(**kwargs):
        # Not a complete response but good enough for our purposes
        rsp = {
            'id': 123,
            'date': '2017-01-01 00:00:00',
            'web_url': 'https://example.com/bundle/123',
            'name': 'Sample bundle',
            'owner': {
                'username': 'foo',
            },
            'project': {
                'name': 'bar',
            },
            'patches': [
                {
                    'id': 42,
                    'date': '2017-01-01 00:00:00',
                    'web_url': 'https://example.com/project/foo/patch/123/',
                    'msgid': '<hello@example.com>',
                    'list_archive_url': None,
                    'name': 'Test',
                    'mbox': 'https://example.com/project/foo/patch/123/mbox/',
                },
            ],
            'public': True,
        }

        rsp.update(**kwargs)

        return rsp

    @mock.patch('git_pw.bundle._get_bundle')
    def test_show(self, mock_get_bundle):
        """Validate standard behavior."""

        rsp = self._get_bundle()
        mock_get_bundle.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(bundle.show_cmd, ['123'])

        assert result.exit_code == 0, result
        mock_get_bundle.assert_called_once_with('123')


@mock.patch('git_pw.api.version', return_value=(1, 0))
@mock.patch('git_pw.api.index')
@mock.patch('git_pw.utils.echo_via_pager')
class ListTestCase(unittest.TestCase):

    @staticmethod
    def _get_bundle(**kwargs):
        return ShowTestCase._get_bundle(**kwargs)

    @staticmethod
    def _get_users(**kwargs):
        rsp = {
            'id': 1,
            'username': 'john.doe',
        }
        rsp.update(**kwargs)
        return rsp

    def test_list(self, mock_echo, mock_index, mock_version):
        """Validate standard behavior."""

        rsp = [self._get_bundle()]
        mock_index.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(bundle.list_cmd, [])

        assert result.exit_code == 0, result
        mock_index.assert_called_once_with('bundles', [
            ('q', None), ('page', None), ('per_page', None),
            ('order', 'name')])

    def test_list_with_formatting(self, mock_echo, mock_index, mock_version):
        """Validate behavior with formatting applied."""

        rsp = [self._get_bundle()]
        mock_index.return_value = rsp

        runner = CLIRunner()
        result = runner.invoke(bundle.list_cmd, [
            '--format', 'simple', '--column', 'ID', '--column', 'Name'])

        assert result.exit_code == 0, result

        mock_echo.assert_called_once_with(mock.ANY, ('ID', 'Name'),
                                          fmt='simple')

    def test_list_with_filters(self, mock_echo, mock_index, mock_version):
        """Validate behavior with filters applied.

        Apply all filters, including those for pagination.
        """

        user_rsp = [self._get_users()]
        bundle_rsp = [self._get_bundle()]
        mock_index.side_effect = [user_rsp, bundle_rsp]

        runner = CLIRunner()
        result = runner.invoke(bundle.list_cmd, [
            '--owner', 'john.doe', '--owner', '2', '--limit', 1, '--page', 1,
            '--sort', '-name', 'test'])

        assert result.exit_code == 0, result
        calls = [
            mock.call('users', [('q', 'john.doe')]),
            mock.call('bundles', [
                ('owner', 1), ('owner', '2'), ('q', 'test'), ('page', 1),
                ('per_page', 1), ('order', '-name')])]

        mock_index.assert_has_calls(calls)

    @mock.patch('git_pw.api.LOG')
    def test_list_with_wildcard_filters(self, mock_log, mock_echo, mock_index,
                                        mock_version):
        """Validate behavior with a "wildcard" filter.

        Patchwork API v1.0 did not support multiple filters correctly. Ensure
        the user is warned as necessary if a filter has multiple matches.
        """

        people_rsp = [self._get_users(), self._get_users()]
        bundle_rsp = [self._get_bundle()]
        mock_index.side_effect = [people_rsp, bundle_rsp]

        runner = CLIRunner()
        runner.invoke(bundle.list_cmd, ['--owner', 'john.doe'])

        assert mock_log.warning.called

    @mock.patch('git_pw.api.LOG')
    def test_list_with_multiple_filters(self, mock_log, mock_echo, mock_index,
                                        mock_version):
        """Validate behavior with use of multiple filters.

        Patchwork API v1.0 did not support multiple filters correctly. Ensure
        the user is warned as necessary if they specify multiple filters.
        """

        people_rsp = [self._get_users()]
        bundle_rsp = [self._get_bundle()]
        mock_index.side_effect = [people_rsp, people_rsp, bundle_rsp]

        runner = CLIRunner()
        result = runner.invoke(bundle.list_cmd, ['--owner', 'john.doe',
                                                 '--owner', 'user.b'])

        assert result.exit_code == 0, result
        assert mock_log.warning.called

    @mock.patch('git_pw.api.LOG')
    def test_list_api_v1_1(self, mock_log, mock_echo, mock_index,
                           mock_version):
        """Validate behavior with API v1.1."""

        mock_version.return_value = (1, 1)

        user_rsp = [self._get_users()]
        bundle_rsp = [self._get_bundle()]
        mock_index.side_effect = [user_rsp, bundle_rsp]

        runner = CLIRunner()
        result = runner.invoke(bundle.list_cmd, [
            '--owner', 'john.doe',
            '--owner', 'user.b',
            '--owner', 'john@example.com'])

        assert result.exit_code == 0, result

        # We should have only made a single call to '/users' (for the user
        # specified by an email address) since API v1.1 supports filtering with
        # usernames natively
        calls = [
            mock.call('users', [('q', 'john@example.com')]),
            mock.call('bundles', [
                ('owner', 'john.doe'), ('owner', 'user.b'), ('owner', 1),
                ('q', None), ('page', None), ('per_page', None),
                ('order', 'name')])]
        mock_index.assert_has_calls(calls)

        # We shouldn't see a warning about multiple versions either
        assert not mock_log.warning.called


@mock.patch('git_pw.api.version', return_value=(1, 2))
@mock.patch('git_pw.api.create')
@mock.patch('git_pw.utils.echo_via_pager')
class CreateTestCase(unittest.TestCase):

    @staticmethod
    def _get_bundle(**kwargs):
        return ShowTestCase._get_bundle(**kwargs)

    def test_create(self, mock_echo, mock_create, mock_version):
        """Validate standard behavior."""

        mock_create.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(bundle.create_cmd, ['hello', '1', '2'])

        assert result.exit_code == 0, result
        mock_create.assert_called_once_with(
            'bundles',
            [('name', 'hello'), ('patches', (1, 2)), ('public', False)]
        )

    def test_create_with_public(self, mock_echo, mock_create, mock_version):
        """Validate behavior with --public option."""

        mock_create.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(bundle.create_cmd, [
            'hello', '1', '2', '--public'])

        assert result.exit_code == 0, result
        mock_create.assert_called_once_with(
            'bundles',
            [('name', 'hello'), ('patches', (1, 2)), ('public', True)]
        )

    @mock.patch('git_pw.api.LOG')
    def test_create_api_v1_1(
        self, mock_log, mock_echo, mock_create, mock_version
    ):

        mock_version.return_value = (1, 1)

        runner = CLIRunner()
        result = runner.invoke(bundle.create_cmd, ['hello', '1', '2'])

        assert result.exit_code == 1, result
        assert mock_log.error.called


@mock.patch('git_pw.api.version', return_value=(1, 2))
@mock.patch('git_pw.api.update')
@mock.patch('git_pw.api.detail')
@mock.patch('git_pw.utils.echo_via_pager')
class UpdateTestCase(unittest.TestCase):

    @staticmethod
    def _get_bundle(**kwargs):
        return ShowTestCase._get_bundle(**kwargs)

    def test_update(self, mock_echo, mock_detail, mock_update, mock_version):
        """Validate standard behavior."""

        mock_update.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(
            bundle.update_cmd,
            ['1', '--name', 'hello', '--patch', '1', '--patch', '2'],
        )

        assert result.exit_code == 0, result
        mock_detail.assert_not_called()
        mock_update.assert_called_once_with(
            'bundles', '1', [('name', 'hello'), ('patches', (1, 2))]
        )

    def test_update_with_public(
        self, mock_echo, mock_detail, mock_update, mock_version,
    ):
        """Validate behavior with --public option."""

        mock_update.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(bundle.update_cmd, ['1', '--public'])

        assert result.exit_code == 0, result
        mock_detail.assert_not_called()
        mock_update.assert_called_once_with('bundles', '1', [('public', True)])

    @mock.patch('git_pw.api.LOG')
    def test_update_api_v1_1(
        self, mock_log, mock_echo, mock_detail, mock_update, mock_version,
    ):

        mock_version.return_value = (1, 1)

        runner = CLIRunner()
        result = runner.invoke(bundle.update_cmd, ['1', '--name', 'hello'])

        assert result.exit_code == 1, result
        assert mock_log.error.called


@mock.patch('git_pw.api.version', return_value=(1, 2))
@mock.patch('git_pw.api.delete')
@mock.patch('git_pw.utils.echo_via_pager')
class DeleteTestCase(unittest.TestCase):

    def test_delete(self, mock_echo, mock_delete, mock_version):
        """Validate standard behavior."""

        mock_delete.return_value = None

        runner = CLIRunner()
        result = runner.invoke(bundle.delete_cmd, ['hello'])

        assert result.exit_code == 0, result
        mock_delete.assert_called_once_with('bundles', 'hello')

    @mock.patch('git_pw.api.LOG')
    def test_delete_api_v1_1(
        self, mock_log, mock_echo, mock_delete, mock_version,
    ):
        """Validate standard behavior."""

        mock_version.return_value = (1, 1)

        runner = CLIRunner()
        result = runner.invoke(bundle.delete_cmd, ['hello'])

        assert result.exit_code == 1, result
        assert mock_log.error.called


@mock.patch('git_pw.api.version', return_value=(1, 2))
@mock.patch('git_pw.api.update')
@mock.patch('git_pw.api.detail')
@mock.patch('git_pw.utils.echo_via_pager')
class AddTestCase(unittest.TestCase):

    @staticmethod
    def _get_bundle(**kwargs):
        return ShowTestCase._get_bundle(**kwargs)

    def test_add(
        self, mock_echo, mock_detail, mock_update, mock_version,
    ):
        """Validate standard behavior."""

        mock_detail.return_value = self._get_bundle()
        mock_update.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(bundle.add_cmd, ['1', '1', '2'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('bundles', '1')
        mock_update.assert_called_once_with(
            'bundles', '1', [('patches', (1, 2, 42))],
        )

    @mock.patch('git_pw.api.LOG')
    def test_add_api_v1_1(
        self, mock_log, mock_echo, mock_detail, mock_update, mock_version,
    ):
        """Validate behavior with API v1.1."""

        mock_version.return_value = (1, 1)

        runner = CLIRunner()
        result = runner.invoke(bundle.add_cmd, ['1', '1', '2'])

        assert result.exit_code == 1, result
        assert mock_log.error.called


@mock.patch('git_pw.api.version', return_value=(1, 2))
@mock.patch('git_pw.api.update')
@mock.patch('git_pw.api.detail')
@mock.patch('git_pw.utils.echo_via_pager')
class RemoveTestCase(unittest.TestCase):

    @staticmethod
    def _get_bundle(**kwargs):
        return ShowTestCase._get_bundle(**kwargs)

    def test_remove(
        self, mock_echo, mock_detail, mock_update, mock_version,
    ):
        """Validate standard behavior."""

        mock_detail.return_value = self._get_bundle(
            patches=[{'id': 1}, {'id': 2}, {'id': 3}],
        )
        mock_update.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(bundle.remove_cmd, ['1', '1', '2'])

        assert result.exit_code == 0, result
        mock_detail.assert_called_once_with('bundles', '1')
        mock_update.assert_called_once_with(
            'bundles', '1', [('patches', (3,))],
        )

    @mock.patch('git_pw.bundle.LOG')
    def test_remove_empty(
        self, mock_log, mock_echo, mock_detail, mock_update, mock_version,
    ):
        """Validate behavior when deleting would remove all patches."""

        mock_detail.return_value = self._get_bundle(
            patches=[{'id': 1}, {'id': 2}, {'id': 3}],
        )
        mock_update.return_value = self._get_bundle()

        runner = CLIRunner()
        result = runner.invoke(bundle.remove_cmd, ['1', '1', '2', '3'])

        assert result.exit_code == 1, result.output
        assert mock_log.error.called
        mock_detail.assert_called_once_with('bundles', '1')
        mock_update.assert_not_called()

    @mock.patch('git_pw.api.LOG')
    def test_remove_api_v1_1(
        self, mock_log, mock_echo, mock_detail, mock_update, mock_version,
    ):
        """Validate behavior with API v1.1."""

        mock_version.return_value = (1, 1)

        runner = CLIRunner()
        result = runner.invoke(bundle.remove_cmd, ['1', '1', '2'])

        assert result.exit_code == 1, result
        assert mock_log.error.called

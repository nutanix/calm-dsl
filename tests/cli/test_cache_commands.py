import pytest
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class TestCacheCommands:
    def test_sync_cache(self):
        runner = CliRunner()
        command = "update cache"
        result = runner.invoke(cli, command)
        LOG.debug(result.output)
        if result.exit_code:
            pytest.fail("Failed to update cache")

    def test_clear_cache(self):
        runner = CliRunner()
        command = "clear cache"
        result = runner.invoke(cli, command)
        LOG.debug(result.output)
        if result.exit_code:
            pytest.fail("Failed to clear cache")

    def test_show_cache(self):
        runner = CliRunner()
        command = "show cache"
        result = runner.invoke(cli, command)
        LOG.debug(result.output)
        if result.exit_code:
            pytest.fail("Failed to show cache")

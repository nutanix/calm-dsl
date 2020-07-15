from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class TestBpCommands:
    def test_bps_list(self):
        runner = CliRunner()
        LOG.info("Invoking 'calm get bps'")
        result = runner.invoke(cli, ["get", "bps"])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response: {}".format(result.output))

    def test_bps_list_with_limit_offset(self):
        runner = CliRunner()
        LOG.info("Invoking 'calm get bps --limit=15 --offset=5'")
        result = runner.invoke(cli, ["get", "bps", "--limit=15", "--offset=5"])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response: {}".format(result.output))

    def test_bps_list_with_name(self):
        runner = CliRunner()
        LOG.info("Invoking 'calm get bps --name=MSSQL'")
        result = runner.invoke(cli, ["get", "bps", "--name=MSSQL"])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response: {}".format(result.output))


if __name__ == "__main__":
    tester = TestBpCommands()
    tester.test_bps_list_with_name()

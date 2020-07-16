import time
from unittest import mock
import pytest
from unittest.mock import MagicMock
from click.testing import CliRunner

from calm.dsl.api.connection import Connection
from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class TestAppCommands:
    def test_apps_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps"])
        assert result.exit_code == 0
        print(result.output)

    def test_apps_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps", "--limit=15", "--offset=5"])
        assert result.exit_code == 0
        print(result.output)

    def test_apps_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps", "--name=MSSQL"])
        assert result.exit_code == 0
        print(result.output)

    @pytest.mark.dependency(depends=["test_bp_describe"])
    @pytest.mark.slow
    def test_bp_launch(self):
        runner = CliRunner()
        self.created_bp_name = "Test_Existing_VM_{}".format(int(time.time()))
        LOG.info("Creating Bp {}".format(self.created_bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file=tests/blueprint_example/test_blueprint_example.py",
                "--name={}".format(self.created_bp_name),
                "--description='Test Blueprint; to delete'",
            ],
        )
        assert result.exit_code == 0
        LOG.info("Success")

        LOG.info("Launching Bp {}".format(self.created_bp_name))
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                self.created_bp_name,
                "--app_name={}_app".format(self.created_bp_name),
            ],
            input="\n".join(["1", "DEV"]),
        )
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug(result.output)

    @mock.patch("calm.dsl.api.connection")
    def test_apps_describe(self, mocked_connection):
        runner = CliRunner()
        connection = Connection("10.46.34.230", "9440", "basic")
        connection._call = MagicMock(side_effect=KeyError("foo"))
        result = runner.invoke(cli, ["get", "apps"])
        # output = result.output
        # import ipdb; ipdb.set_trace()
        # result = runner.invoke(cli, ["describe", "apps"])
        assert result.exit_code == 0
        print(result.output)


if __name__ == "__main__":
    tester = TestAppCommands()
    tester.test_apps_describe()

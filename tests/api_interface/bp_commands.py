import pytest
from click.testing import CliRunner

from calm.dsl.cli import main as cli


def test_bps_list(self):
    runner = CliRunner()
    result = runner.invoke(cli, ["get", "bps"])
    assert result.exit_code == 0
    if result.exit_code:
        pytest.fail("BP Get failed")
    pytest.fail("Dummy test failure")
    print(result.output)


class TestBpCommands:
    def test_bps_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("BP Get failed")
        pytest.fail("Dummy test failure")
        print(result.output)

    def test_bps_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps", "--limit=15", "--offset=5"])
        assert result.exit_code == 0
        print(result.output)

    def test_bps_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps", "--name=MSSQL"])
        assert result.exit_code == 0
        print(result.output)


if __name__ == "__main__":
    tester = TestBpCommands()
    tester.test_bps_list_with_name()

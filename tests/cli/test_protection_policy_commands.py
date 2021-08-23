import pytest
import json
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


@pytest.mark.slow
class TestProtectionPolicyCommands:
    def test_protection_policies_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "protection_policies"])
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Protection Policy List failed")
        LOG.info("Success")


if __name__ == "__main__":
    tester = TestProtectionPolicyCommands()

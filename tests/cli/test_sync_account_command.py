import pytest
import json
import traceback
from click.testing import CliRunner
from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins import read_local_file

LOG = get_logging_handle(__name__)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
ACCOUNT_NAME = DSL_CONFIG["ACCOUNTS"]["NUTANIX_PC"][0]["NAME"]


class TestSyncAccountCommand:
    def test_sync_account(self):
        """Syncs an account by the account_name"""

        runner = CliRunner()
        LOG.info("Testing 'calm sync account {}".format(ACCOUNT_NAME))
        result = runner.invoke(
            cli,
            ["sync", "account", ACCOUNT_NAME],
        )

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
            pytest.fail("Account sync failed")

        LOG.info("Success")

import pytest
import json
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class TestAccounts:
    @pytest.mark.parametrize(
        "account_file",
        [
            "tests/accounts/test_ahv_account.py",
            "tests/accounts/test_aws_account.py",
            "tests/accounts/test_azure_account.py",
            "tests/accounts/test_k8s_basic_auth_account.py",
            "tests/accounts/test_k8s_ca_cert_auth_account.py",
            "tests/accounts/test_k8s_client_cert_auth_account.py",
            "tests/accounts/test_k8s_karbon_account.py",
            "tests/accounts/test_vmware_account.py",
        ],
    )
    def test_compile(self, account_file):
        """
        Tests compile command on accounts
        NOTE: test_k8s_karbon_account may fail due to cluster not present on server
        """

        runner = CliRunner()
        LOG.info("Compiling account file at {}".format(account_file))
        result = runner.invoke(
            cli, ["compile", "account", "--file={}".format(account_file)]
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
            pytest.fail("Account compile command failed")
        LOG.info("Success")

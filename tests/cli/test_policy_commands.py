import pytest
import time
import json
import traceback
from click.testing import CliRunner
from distutils.version import LooseVersion as LV

from calm.dsl.config import get_context
from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version

LOG = get_logging_handle(__name__)

CALM_VERSION = Version.get_version("Calm")
DSL_POLICY_FILEPATH = "tests/policy/approval_policy.py"


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.4.0"),
    reason="Approval policy is supported from 3.4.0",
)
class TestPolicyCommands:
    @classmethod
    def setup_class(cls):
        context_obj = get_context()
        policy_config = context_obj.get_policy_config()
        if policy_config.get("policy_status", "False") == "False":
            pytest.skip("policy not enabled")

    def test_compile_policy(self):
        runner = CliRunner()
        LOG.info("Compiling Policy file at {}".format(DSL_POLICY_FILEPATH))
        result = runner.invoke(
            cli, ["compile", "policy", "--file={}".format(DSL_POLICY_FILEPATH)]
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
            pytest.fail("Policy compile command failed")
        LOG.info("Success")

    def test_dsl_policy_create(self):
        runner = CliRunner()
        self.created_dsl_policy_name = "Test_Policy_Create_DSL_{}".format(
            int(time.time())
        )
        LOG.info("Creating Policy {}".format(self.created_dsl_policy_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "policy",
                "--file={}".format(DSL_POLICY_FILEPATH),
                "--name={}".format(self.created_dsl_policy_name),
                "--description='Test DSL Policy: to create'",
            ],
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
            pytest.fail("Policy creation from python file failed")
        LOG.info("Success")
        self._test_policy_describe()

    def _test_policy_describe(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["describe", "policy", self.created_dsl_policy_name]
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
        self._test_dsl_policy_delete()

    def _test_dsl_policy_delete(self):
        runner = CliRunner()
        LOG.info("Deleting DSL Bp {} ".format(self.created_dsl_policy_name))
        result = runner.invoke(cli, ["delete", "policy", self.created_dsl_policy_name])
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
        LOG.info("Success")

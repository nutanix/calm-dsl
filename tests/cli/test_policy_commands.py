import pytest
import time
import json
import traceback
import uuid
from click.testing import CliRunner
from distutils.version import LooseVersion as LV

from calm.dsl.config import get_context
from calm.dsl.cli import approval_request_commands, main as cli
from tests.utils import get_approval_project
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version
from calm.dsl.builtins import read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
LOG = get_logging_handle(__name__)

CALM_VERSION = Version.get_version("Calm")
DSL_POLICY_FILEPATH = "tests/policy/approval_policy.py"
DSL_POLICY_WITH_EMPTY_FIELDS = "tests/policy/approval_policy_with_empty_fields.py"
DSL_POLICY_UNICODE = "tests/policy/approval_policy_with_unicode.py"
DSL_POLICY_UNICODE_UPDATED = "tests/policy/approval_policy_with_unicode_updated.py"
DSL_AHV_POLICY = "examples/APPROVAL_POLICY/ahv_policy.py"
DSL_AWS_POLICY = "examples/APPROVAL_POLICY/aws_policy.py"
DSL_AZURE_POLICY = "examples/APPROVAL_POLICY/azure_policy.py"
DSL_GCP_POLICY = "examples/APPROVAL_POLICY/gcp_policy.py"
DSL_VMWARE_POLICY = "examples/APPROVAL_POLICY/vmware_policy.py"
DSL_POLICY_APP_LAUNCH = "tests/policy/approval_policy_app_launch.py"
DSL_POLICY_RUNBOOK_LAUNCH = "examples/APPROVAL_POLICY/approval_policy_runbook.py"
DSL_POLICY_APP_LAUNCH_APPROVAL_FLOW = "tests/policy/approval_policy_flow_app_launch.py"
DSL_POLICY_RUNBOOK_APPROVAL_FLOW = "tests/policy/approval_policy_flow_runbook_launch.py"
DSL_POLICY_RUNBOOK_FILTERS = "tests/policy/approval_policy_test_filters_runbook.py"
DSL_POLICY_DAY2 = "examples/APPROVAL_POLICY/approval_policy_day2_actions.py"
DSL_RUNBOOK_FILEPATH = "examples/Runbooks/runbook_approval_policy_entity_stats.py"
DSL_AHV_BP = "tests/blueprint_example/test_ahv_bp/blueprint.py"
DSL_AWS_BP = "tests/blueprint_example/test_aws_bp/blueprint.py"
DSL_VMWARE_BP = "tests/blueprint_example/test_vmware_bp/blueprint.py"
DSL_DAY2_BP = "tests/blueprint_example/test_bp_dayTwo/blueprint.py"


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.5.0"),
    reason="Approval policy is supported from 3.5.0",
)
class TestPolicyCommands:
    @classmethod
    def setup_class(cls):
        context_obj = get_context()
        policy_config = context_obj.get_policy_config()
        if policy_config.get("policy_status", "False") == "False":
            pytest.skip("policy not enabled")

    def setup_method(self):
        ContextObj = get_context()

        POLICY_PROJECT = get_approval_project(DSL_CONFIG)
        ContextObj.update_project_context(POLICY_PROJECT)

    def teardown_method(self):
        ContextObj = get_context()
        ContextObj.reset_configuration()

        if self.created_dsl_policy_name:
            self._test_dsl_policy_delete()

        self.created_dsl_policy_name = ""

    def test_compile_policy(self):
        self.created_dsl_policy_name = ""
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

    def test_approval_policy_with_empty_fields(self):

        runner = CliRunner()
        self.created_dsl_policy_name = "Test_Policy_Create_DSL_{}".format(
            str(uuid.uuid4())
        )
        LOG.info("Creating Policy {}".format(self.created_dsl_policy_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "policy",
                "--file={}".format(DSL_POLICY_WITH_EMPTY_FIELDS),
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
            assert (
                str(result.exception) == "Policy event name not provided"
            ), "Policy creation should be unsuccessfull"

        LOG.info("Success")

    def test_approval_policy_with_unicode(self):

        runner = CliRunner()
        self.created_dsl_policy_name = "Test_Policy_Create_DSL_ĠÀÁÆËÌÍÎÏD0Ð_{}".format(
            str(uuid.uuid4())
        )
        LOG.info("Creating Policy {}".format(self.created_dsl_policy_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "policy",
                "--file={}".format(DSL_POLICY_UNICODE),
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
        assert (
            self.created_dsl_policy_name in result.output
        ), "Creation of policy with unicode name failed from DSL"
        self._test_policy_check_in_get_policies()
        self._test_dsl_policy_enable()
        self._test_dsl_policy_update(DSL_POLICY_UNICODE_UPDATED)

    @pytest.mark.parametrize(
        "policy",
        [
            DSL_AHV_POLICY,
            DSL_AWS_POLICY,
            DSL_AZURE_POLICY,
            DSL_GCP_POLICY,
            DSL_VMWARE_POLICY,
            DSL_POLICY_APP_LAUNCH,
            DSL_POLICY_RUNBOOK_LAUNCH,
        ],
    )
    def test_approval_policy_create_flow(self, policy):
        self._test_dsl_policy_create(policy)
        self._test_policy_check_in_get_policies()

    @pytest.mark.parametrize(
        "policy",
        [DSL_POLICY_RUNBOOK_APPROVAL_FLOW],
    )
    def test_policy_approval_flow_runbook(self, policy):

        self._test_dsl_policy_create(policy)
        self._create_and_launch_runbook()
        self._test_get_approval_requests()
        self._get_uuid_in_describe_approval_request()
        self._test_execution_check_in_get_policy_execution()
        self._test_approve_policy()
        self._test_describe_approval_request()
        self._test_approve_approved_policy()

    @pytest.mark.parametrize(
        "policy, blueprint",
        [
            (DSL_AHV_POLICY, DSL_AHV_BP),
            (DSL_AWS_POLICY, DSL_AWS_BP),
            (DSL_VMWARE_POLICY, DSL_VMWARE_BP),
        ],
    )
    def test_policy_approval_flow_app(self, policy, blueprint):

        self._test_dsl_policy_create(policy)
        self._test_dsl_policy_enable()
        self._create_and_launch_app(blueprint)
        self._test_get_approval_requests()
        self._test_approve_policy()

    def test_policy_approval_day_two_action(self):

        self._test_dsl_policy_create(DSL_POLICY_DAY2)
        self._test_dsl_policy_enable()
        self._create_and_launch_app(DSL_DAY2_BP)
        self._run_day2_action()
        self._test_get_approval_requests()
        self._test_approve_policy()

    @pytest.mark.parametrize(
        "policy",
        [DSL_POLICY_RUNBOOK_FILTERS],
    )
    def test_approval_list_filters(self, policy):

        self._test_dsl_policy_create(policy)
        self._create_and_launch_runbook("rb_approval_filters")
        self._test_get_approval_requests()
        self._test_name_filter_in_get_approval_request()
        self._test_time_filter_in_get_approval_policy()
        self._test_approve_policy()
        self._test_approved_filter_in_get_approval_request()

    def _test_dsl_policy_create(self, dsl_filepath=DSL_POLICY_FILEPATH):
        runner = CliRunner()
        self.created_dsl_policy_name = "Test_Policy_Create_DSL{}".format(
            str(uuid.uuid4())
        )
        LOG.info("Creating Policy {}".format(self.created_dsl_policy_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "policy",
                "--file={}".format(dsl_filepath),
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
        assert (
            self.created_dsl_policy_name in result.output
        ), "Policy Creation from python file failed"
        LOG.info("Success")

    def _test_policy_check_in_get_policies(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "policies"])
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy get call failed")
        assert (
            self.created_dsl_policy_name in result.output
        ), "No Policy found with name {}".format(self.created_dsl_policy_name)
        LOG.info("Success")

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
            pytest.fail("Policy describe failed")

    def _test_dsl_policy_enable(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["enable", "policy", self.created_dsl_policy_name])

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
            pytest.fail("Policy enable from python file failed")
        assert "ENABLED" in result.output, "Policy enablement from python unsuccessfull"
        LOG.info("Success")

    def _test_dsl_policy_update(self, dsl_filepath=DSL_POLICY_FILEPATH):
        runner = CliRunner()
        LOG.info("Updating Policy {}".format(self.created_dsl_policy_name))
        result = runner.invoke(
            cli,
            [
                "update",
                "policy",
                "--file={}".format(dsl_filepath),
                "--name={}".format(self.created_dsl_policy_name),
                "--description='Test DSL Policy: to update'",
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
            pytest.fail("Policy update from python file failed")
        LOG.info(result.output)
        LOG.info("Success")

    def _test_dsl_policy_delete(self):
        runner = CliRunner()
        LOG.info("Deleting DSL policy {} ".format(self.created_dsl_policy_name))
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

    def _test_get_approval_requests(self):
        time.sleep(10)
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "approval-requests"])
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy get approval request call from python file failed")
        assert (
            self.approval_request_name in result.output
        ), "Approval Request {} not found".format(self.approval_request_name)
        LOG.info("Success")

    def _test_execution_check_in_get_policy_execution(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["get", "policy-executions", self.created_dsl_policy_name]
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy execution history failed")
        assert (
            self.created_dsl_runbook_name in result.output
        ), "calm get policy-executions failed"
        LOG.info("Success")

    def _test_name_filter_in_get_approval_request(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["get", "approval-requests", "--name", self.approval_request_name]
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy Execution history failed")
        assert (
            self.approval_request_name in result.output
        ), "Filtering approval request on the basis of name failed"
        LOG.info("Success")

    def _test_approved_filter_in_get_approval_request(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "get",
                "approval-requests",
                "-a",
                "-f",
                "state==APPROVED",
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy approval filter failed")
        assert (
            self.approval_request_name in result.output
        ), "Filtering approval request on the basis of approval status failed"
        LOG.info("Success")

    def _test_time_filter_in_get_approval_policy(self):
        current_time = int(time.time())
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "get",
                "approval-requests",
                "--filter",
                "creation_time=le={};creation_time=ge={}".format(
                    (current_time * 1000000), ((current_time - 120) * 1000000)
                ),
            ],
        )

        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy approval time filter failed")
        assert (
            self.approval_request_name in result.output
        ), "Filtering approval request on the basis of time of creation failed"
        LOG.info("Success")

    def _test_approve_policy(self, uuid=None):
        LOG.info(self.approval_request_name)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "approve",
                "approval-request",
                self.approval_request_name,
            ],
        )

        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy approval from dsl failed")

        assert "APPROVED" in result.output, "Failed approving approval request from DSL"

    def _test_approve_approved_policy(self, uuid=None):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "approve",
                "approval-request",
                self.approval_request_name,
            ],
        )

        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Already approved requests should not be approved ")
        LOG.info("Success")

    def _test_describe_approval_request(self):

        runner = CliRunner()
        result = runner.invoke(
            cli, ["describe", "approval-request", self.approval_request_name]
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
        assert (
            "Policy: {}".format(self.created_dsl_policy_name) in result.output
        ), "calm desctibe approval-request failed"
        assert (
            "Requested By: admin" in result.output
        ), "Assertion of owner referance failed"

    def _get_uuid_in_describe_approval_request(self):
        runner = CliRunner()

        result = runner.invoke(
            cli, ["describe", "approval-request", self.approval_request_name]
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
        var1 = result.output.split("Status")[0]
        self.uuid = var1.split("uuid:")[1].split(")")[0]
        result = runner.invoke(
            cli,
            [
                "get",
                "approval-requests",
                "--name",
                self.approval_request_name,
                "--filter",
                "uuid=={}".format(str(self.uuid.strip())),
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(result.output)
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            pytest.fail("Policy uuid filter for approval-request failed")

        assert (
            self.uuid in result.output
        ), "Filtering approval request on the basis of UUID failed"

    def _create_and_launch_runbook(self, rb_name="rb_policy_approval_"):
        self.created_dsl_runbook_name = rb_name + "{}".format(str(uuid.uuid4()))
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "runbook",
                "--file={}".format(DSL_RUNBOOK_FILEPATH),
                "--name={}".format(self.created_dsl_runbook_name),
            ],
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "runbook",
                self.created_dsl_runbook_name,
            ],
            input="\n",
        )
        self.approval_request_name = "Execute Runbook " + self.created_dsl_runbook_name

    def _create_and_launch_app(self, bp_filepath):
        self.created_bp_name = "bp_policy_approval_{}".format(str(uuid.uuid4()))
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_filepath),
                "--name={}".format(self.created_bp_name),
            ],
        )

        self.created_app_name = "App-" + self.created_bp_name
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                self.created_bp_name,
                "--app_name={}".format(self.created_app_name),
                "--ignore_runtime_variables",
            ],
        )
        self.approval_request_name = "Launch App " + self.created_app_name

    def _run_day2_action(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "update",
                "app",
                self.created_app_name,
                "patch_update1",
                "--ignore_runtime_variables",
            ],
        )
        self.approval_request_name = "Day_two_operation App " + self.created_app_name

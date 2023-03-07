import pytest
import json
import uuid
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.cli.task_commands import watch_task
from calm.dsl.cli.constants import ERGON_TASK
from calm.dsl.builtins import read_local_file
from calm.dsl.api import get_api_client
from calm.dsl.builtins.models.helper.common import get_project
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
CREATE_PROJECT_FILE_LOCATION = "tests/project/sample_files/project_for_create.py"
UPDATE_PROJECT_FILE_LOCATION = "tests/project/sample_files/project_for_update.py"
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

ACCOUNTS = DSL_CONFIG["ACCOUNTS"]["NUTANIX_PC"]

NTNX_LOCAL_AZ = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
MULTIPC_ACCOUNT = [
    account for account in ACCOUNTS if account["NAME"].startswith("multipc_account")
][0]

USER1 = DSL_CONFIG["USERS"][0]["NAME"]
USER2 = DSL_CONFIG["USERS"][1]["NAME"]
UPDATED_USERS_NAME = [USER1, USER2]

USER_GROUP1 = DSL_CONFIG["USER_GROUPS"][0]["NAME"]
USER_GROUP2 = DSL_CONFIG["USER_GROUPS"][1]["NAME"]
UPDATED_GROUPS_NAME = [USER_GROUP1, USER_GROUP2]

SUBNET1 = MULTIPC_ACCOUNT["SUBNETS"][0]["NAME"]
SUBNET2 = NTNX_LOCAL_AZ["SUBNETS"][0]["NAME"]
UPDATED_SUBNET_NAME = [SUBNET1, SUBNET2]

ACCOUNT_NAME1 = MULTIPC_ACCOUNT["NAME"]
ACCOUNT_NAME2 = NTNX_LOCAL_AZ["NAME"]
UPDATED_ACCOUNT_NAME = [ACCOUNT_NAME1, ACCOUNT_NAME2]

CLUSTER_UUID1 = MULTIPC_ACCOUNT["SUBNETS"][0]["CLUSTER_UUID"]
CLUSTER_UUID2 = NTNX_LOCAL_AZ["SUBNETS"][0]["CLUSTER_UUID"]
UPDATED_CLUSTER_UUID = [CLUSTER_UUID1, CLUSTER_UUID2]


class TestProjectUpdate:
    def setup_method(self):
        """Method to create a project for testing the update project"""

        self.project_name = "test_proj" + str(uuid.uuid4())[-10:]
        runner = CliRunner()
        LOG.info("Compiling Project file at {}".format(CREATE_PROJECT_FILE_LOCATION))
        result = runner.invoke(
            cli,
            ["compile", "project", "--file={}".format(CREATE_PROJECT_FILE_LOCATION)],
        )

        if result.exit_code:
            pytest.fail("[{}] - {}".format(result.output, str(result.exception)))

        self.project_payload = json.loads(result.output)
        self.project_payload["spec"]["name"] = self.project_name
        self.project_payload["metadata"]["name"] = self.project_name

        client = get_api_client()

        # Create API
        LOG.info("Creating project {}".format(self.project_name))
        res, err = client.project.create(self.project_payload)
        self.project_uuid = res.json()["metadata"]["uuid"]
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        else:
            res = res.json()
            task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
            if task_state in ERGON_TASK.FAILURE_STATES:
                pytest.fail("Project creation task went to {} state".format(task_state))
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))
            LOG.info("PROJECT NAME:{}".format(self.project_name))

    def teardown_method(self):
        """Method to delete project after testing the update project"""

        client = get_api_client()
        res, err = client.project.delete(self.project_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        else:
            res = res.json()
            task_state = watch_task(res["status"]["execution_context"]["task_uuid"])
            if task_state in ERGON_TASK.FAILURE_STATES:
                pytest.fail("Project deletion task went to {} state".format(task_state))
            LOG.info("Success")
            LOG.debug("Response: {}".format(res))

    def update_test_data(self):
        """Helper to get updated users and groups"""

        client = get_api_client()
        project_data = get_project(self.project_name)

        self.updated_users = []
        self.updated_groups = []
        self.updated_subnets = []
        self.updated_accounts = []
        self.updated_vpcs = []
        self.updated_clusters = []

        for _user in project_data["spec"]["resources"]["user_reference_list"]:
            self.updated_users.append(_user["name"])

        for _group in project_data["spec"]["resources"][
            "external_user_group_reference_list"
        ]:
            self.updated_groups.append(_group["name"])

        for _subnet in project_data["spec"]["resources"]["subnet_reference_list"]:
            self.updated_subnets.append(_subnet["name"])

        for _external_network in project_data["spec"]["resources"][
            "external_network_list"
        ]:
            self.updated_subnets.append(_external_network["name"])

        for _account in project_data["spec"]["resources"]["account_reference_list"]:
            res, err = client.account.read(_account["uuid"])
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))
            self.updated_accounts.append(res.json()["metadata"]["name"])

        for _cluster in project_data["spec"]["resources"]["cluster_reference_list"]:
            self.updated_clusters.append(_cluster["uuid"])

    def test_update_project_with_append_only(self):
        """tests project update with --append-only flag"""

        runner = CliRunner()
        LOG.info(
            "Updating Project using file at {}".format(UPDATE_PROJECT_FILE_LOCATION)
        )
        result = runner.invoke(
            cli,
            [
                "update",
                "project",
                self.project_name,
                "--file={}".format(UPDATE_PROJECT_FILE_LOCATION),
                "--append-only",
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
            pytest.fail("Project update command failed")

        self.update_test_data()

        assert len(self.updated_users) == len(UPDATED_USERS_NAME)
        assert set(self.updated_users) == set(UPDATED_USERS_NAME)

        assert len(self.updated_groups) == len(UPDATED_GROUPS_NAME)
        assert set(self.updated_groups) == set(UPDATED_GROUPS_NAME)

        assert len(self.updated_subnets) == len(UPDATED_SUBNET_NAME)
        assert set(self.updated_subnets) == set(UPDATED_SUBNET_NAME)

        assert len(self.updated_accounts) == len(UPDATED_ACCOUNT_NAME)
        assert set(self.updated_accounts) == set(UPDATED_ACCOUNT_NAME)

        assert len(self.updated_clusters) == len(UPDATED_CLUSTER_UUID)
        assert set(self.updated_clusters) == set(UPDATED_CLUSTER_UUID)

import pytest
import json
import uuid
import traceback
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.cli.environments import get_environment_by_uuid
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins.models.helper.common import get_project
from calm.dsl.api import get_api_client
from calm.dsl.store import Version
from calm.dsl.config import get_context
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_PROJECT_PATH = "tests/3_2_0/project/project_with_multi_env.py"
DSL_UPDATE_PROJECT_PATH = "tests/3_2_0/project/project_with_multi_env_update.py"
DSL_ENVIRONMENT_PATH = "tests/3_2_0/project/sample_environment.py"
ENV_1_NAME = "ProjEnvironment1"
ENV_2_NAME = "ProjEnvironment2"
ENV_3_NAME = "ProjEnvironment3"

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
SQL_SERVER_IMAGE = DSL_CONFIG["AHV"]["IMAGES"]["CD_ROM"]["SQL_SERVER_2014_x64"]

# Accounts
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]

NTNX_ACCOUNT_1 = ACCOUNTS["NUTANIX_PC"][0]
NTNX_ACCOUNT_1_UUID = NTNX_ACCOUNT_1["UUID"]
NTNX_ACCOUNT_1_SUBNET_1_UUID = NTNX_ACCOUNT_1["SUBNETS"][0]["UUID"]
NTNX_ACCOUNT_1_SUBNET_2_UUID = NTNX_ACCOUNT_1["SUBNETS"][1]["UUID"]

NTNX_ACCOUNT_2 = ACCOUNTS["NUTANIX_PC"][1]
NTNX_ACCOUNT_2_UUID = NTNX_ACCOUNT_2["UUID"]
NTNX_ACCOUNT_2_SUBNET_1_UUID = NTNX_ACCOUNT_2["SUBNETS"][0]["UUID"]
NTNX_ACCOUNT_2_SUBNET_2_UUID = NTNX_ACCOUNT_2["SUBNETS"][1]["UUID"]

AWS_ACCOUNT = ACCOUNTS["AWS"][0]
AWS_ACCOUNT_UUID = AWS_ACCOUNT["UUID"]

AZURE_ACCOUNT = ACCOUNTS["AZURE"][0]
AZURE_ACCOUNT_UUID = AZURE_ACCOUNT["UUID"]

GCP_ACCOUNT = ACCOUNTS["GCP"][0]
GCP_ACCOUNT_UUID = GCP_ACCOUNT["UUID"]

VMWARE_ACCOUNT = ACCOUNTS["VMWARE"][0]
VMWARE_ACCOUNT_UUID = VMWARE_ACCOUNT["UUID"]

K8S_ACCOUNT = ACCOUNTS["K8S"][0]
K8S_ACCOUNT_UUID = K8S_ACCOUNT["UUID"]

USER = DSL_CONFIG["USERS"][0]
USER_UUID = USER["UUID"]

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.2.0"),
    reason="Tests are for env changes introduced in 3.2.0",
)
class TestProjectEnv:
    def setup_method(self):
        """Method to instantiate variable for projects to be deleted"""

        self.project_deleted = False
        self.project_name = None

        # Reset the context changes
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

    def teardown_method(self):
        """Method to delete project if not deleted during tests"""

        # Reset the context changes
        ContextObj = get_context()
        ContextObj.reset_configuration()

        if self.project_name and (not self.project_deleted):
            self._test_delete_project()

        # Resetting metadata object
        reset_metadata_obj()

    def test_env_infra_presence_in_compiled_payload(self):
        """test to check env infra presence in project compiled payload"""

        runner = CliRunner()
        LOG.info("Compiling Project file at {}".format(DSL_PROJECT_PATH))
        result = runner.invoke(
            cli, ["-vvvvv", "compile", "project", "--file={}".format(DSL_PROJECT_PATH)]
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
            pytest.fail("Project compile command failed")

        res_out = result.output

        # data assertions
        assert NTNX_ACCOUNT_1_UUID in res_out
        assert NTNX_ACCOUNT_1_SUBNET_1_UUID in res_out
        assert NTNX_ACCOUNT_1_SUBNET_2_UUID in res_out
        assert NTNX_ACCOUNT_2_SUBNET_1_UUID in res_out
        assert NTNX_ACCOUNT_2_SUBNET_2_UUID not in res_out  # Negative case
        assert AWS_ACCOUNT_UUID in res_out
        assert AZURE_ACCOUNT_UUID in res_out
        assert GCP_ACCOUNT_UUID in res_out
        assert K8S_ACCOUNT_UUID in res_out
        assert USER_UUID in res_out

        LOG.info("Success")

    def update_test_data(self):
        """Helper to update test data env_uuids"""

        client = get_api_client()
        project_data = get_project(self.project_name)
        self.project_uuid = project_data["metadata"]["uuid"]

        env_payload = {
            "length": 250,
            "offset": 0,
            "filter": "project_reference=={}".format(self.project_uuid),
        }
        env_name_uuid_map = client.environment.get_name_uuid_map(env_payload)

        self.env1_uuid = env_name_uuid_map.get(ENV_1_NAME, "")
        self.env2_uuid = env_name_uuid_map.get(ENV_2_NAME, "")
        self.env3_uuid = env_name_uuid_map.get(ENV_3_NAME, "")

    def test_create_project(self):
        """tests creation of project"""

        runner = CliRunner()
        self.project_name = "DSL_PROJECT_{}".format(str(uuid.uuid4())[-10:])

        LOG.info("Creating Project using file at {}".format(DSL_PROJECT_PATH))
        result = runner.invoke(
            cli,
            [
                "create",
                "project",
                "--file={}".format(DSL_PROJECT_PATH),
                "--name={}".format(self.project_name),
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
            pytest.fail("Project create command failed")

        # Update internal project data
        self.update_test_data()

        self._test_project_describe_out_text()

        self._test_project_data()

        self._test_env_data()

        self._test_get_environments()

        self._test_compile_environment()

        self._test_update_environment_1()

        self._test_create_environment()

        self._test_delete_environment()

        self._test_env_removal_on_projects_update_dsl()

        self._test_delete_project()

    def _test_env_removal_on_projects_update_dsl(self):
        """tests whether updating project through dsl will not delete existing environment"""

        runner = CliRunner()
        project_data = get_project(self.project_name)
        existing_env_uuids = [
            _env["uuid"]
            for _env in project_data["spec"]["resources"]["environment_reference_list"]
        ]

        LOG.info("Updating Project using file at {}".format(DSL_UPDATE_PROJECT_PATH))
        result = runner.invoke(
            cli,
            [
                "update",
                "project",
                self.project_name,
                "--file={}".format(DSL_UPDATE_PROJECT_PATH),
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

        LOG.info("Checking presence of environments in project")
        project_data = get_project(self.project_name)
        project_str = json.dumps(project_data)
        new_env_uuids = [
            _env["uuid"]
            for _env in project_data["spec"]["resources"]["environment_reference_list"]
        ]
        assert (env_uuid in new_env_uuids for env_uuid in existing_env_uuids)
        assert NTNX_ACCOUNT_2_UUID not in project_str
        assert NTNX_ACCOUNT_2_SUBNET_1_UUID not in project_str

    def _test_env_data(self):
        """tests env data i.e. accounts, subnets in project-environments"""

        LOG.info("Checking presence of accounts and subnets in created environments")

        project_data = get_project(self.project_name)

        # Check if there are two envs present there
        assert (
            len(
                project_data["status"]["resources"].get(
                    "environment_reference_list", []
                )
            )
            == 2
        )

        env_refs = project_data["status"]["resources"].get(
            "environment_reference_list", []
        )
        for _env in env_refs:
            env_data = get_environment_by_uuid(_env["uuid"])
            env_str = json.dumps(env_data)

            if env_data["spec"]["name"] == ENV_1_NAME:
                assert NTNX_ACCOUNT_1_UUID in env_str
                assert NTNX_ACCOUNT_1_SUBNET_1_UUID in env_str
                assert AWS_ACCOUNT_UUID in env_str
                assert AZURE_ACCOUNT_UUID in env_str

            elif env_data["spec"]["name"] == ENV_2_NAME:
                assert NTNX_ACCOUNT_2_UUID in env_str
                assert NTNX_ACCOUNT_2_SUBNET_1_UUID in env_str
                assert GCP_ACCOUNT_UUID in env_str
                assert AZURE_ACCOUNT_UUID not in env_str

    def _test_project_describe_out_text(self):
        """tests describe command on project"""

        runner = CliRunner()
        LOG.info("Testing 'calm describe project --out text' command")
        result = runner.invoke(cli, ["describe", "project", self.project_name])
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
            pytest.fail("Project Get call failed")

        project_name_str = "Name: {}".format(self.project_name)
        assert project_name_str in result.output
        LOG.info("Success")

    def _test_project_data(self):
        """tests project data i.e. accounts, subnets in project"""

        LOG.info("Checking presence of accounts and subnets in created project")
        project_data = get_project(self.project_name)
        project_str = json.dumps(project_data)

        assert NTNX_ACCOUNT_1_UUID in project_str
        assert NTNX_ACCOUNT_1_SUBNET_1_UUID in project_str
        assert NTNX_ACCOUNT_1_SUBNET_2_UUID in project_str
        assert NTNX_ACCOUNT_2_SUBNET_1_UUID in project_str
        assert NTNX_ACCOUNT_2_SUBNET_2_UUID not in project_str  # Negative case
        assert AWS_ACCOUNT_UUID in project_str
        assert AZURE_ACCOUNT_UUID in project_str
        assert GCP_ACCOUNT_UUID in project_str
        assert K8S_ACCOUNT_UUID in project_str
        assert USER_UUID in project_str

    def _test_delete_project(self):
        """tests deletion of project"""

        runner = CliRunner()

        # Project should not be deleted if deleted in test.
        # if deletion of project fails here, it will allso fail at testdown method
        # so assigning it to true before starting deletion of project
        self.project_deleted = True

        LOG.info("Deleting Project {}".format(self.project_name))
        result = runner.invoke(cli, ["delete", "project", self.project_name])

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
            pytest.fail("Project deletion command failed")

    def _test_get_environments(self):
        """tests listing of environments command"""

        runner = CliRunner()
        LOG.info("Listing environments for project {}".format(self.project_name))
        result = runner.invoke(
            cli, ["get", "environments", "--project", self.project_name]
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
            pytest.fail("Environments get command failed")

        assert self.env1_uuid in result.output
        assert self.env2_uuid in result.output

    def _test_delete_environment(self):
        """tests deletion of environment"""

        runner = CliRunner()
        LOG.info("Deleting Environment {}".format(ENV_2_NAME))
        result = runner.invoke(
            cli, ["delete", "environment", ENV_2_NAME, "--project", self.project_name]
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
            pytest.fail("Environment deletion command failed")

    def _test_update_environment_1(self):
        """
        It tests environment update command
        Summary: Following updates will happen
            1. GCP and VMWARE accounts will be added
            2. AZURE account will be removed
        """

        env_data = get_environment_by_uuid(self.env1_uuid)
        env_account_uuids = []

        for _obj in env_data["spec"]["resources"]["infra_inclusion_list"]:
            env_account_uuids.append(_obj["account_reference"]["uuid"])

        # gcp and vmware account are not whitelisted in environment
        assert AZURE_ACCOUNT_UUID in env_account_uuids
        assert GCP_ACCOUNT_UUID not in env_account_uuids
        assert VMWARE_ACCOUNT_UUID not in env_account_uuids

        LOG.info(
            "Updating environment {} using file at {}".format(
                ENV_1_NAME, DSL_ENVIRONMENT_PATH
            )
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "update",
                "environment",
                ENV_1_NAME,
                "--file={}".format(DSL_ENVIRONMENT_PATH),
                "--project={}".format(self.project_name),
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
            pytest.fail("Environment update command failed")

        env_new_data = get_environment_by_uuid(self.env1_uuid)
        env_new_account_uuids = []

        for _obj in env_new_data["spec"]["resources"]["infra_inclusion_list"]:
            env_new_account_uuids.append(_obj["account_reference"]["uuid"])

        # During updation we added gcp and vmware  and removed azure accounts to environment
        assert GCP_ACCOUNT_UUID in env_new_account_uuids
        assert VMWARE_ACCOUNT_UUID in env_new_account_uuids
        assert NTNX_ACCOUNT_1_UUID in env_new_account_uuids
        assert AWS_ACCOUNT_UUID in env_new_account_uuids
        assert AZURE_ACCOUNT_UUID not in env_new_account_uuids

    def _test_compile_environment(self):
        """
        Test compiles enivoronment to existing project
        """

        runner = CliRunner()
        LOG.info("Compiling environment using file at {}".format(DSL_PROJECT_PATH))
        result = runner.invoke(
            cli,
            [
                "compile",
                "environment",
                "--file={}".format(DSL_ENVIRONMENT_PATH),
                "--project={}".format(self.project_name),
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
            pytest.fail("Environment compile command failed")

        env_str = result.output
        assert NTNX_ACCOUNT_1_UUID in env_str
        assert NTNX_ACCOUNT_1_SUBNET_1_UUID in env_str
        assert NTNX_ACCOUNT_1_SUBNET_2_UUID not in env_str
        assert NTNX_ACCOUNT_2_SUBNET_1_UUID not in env_str
        assert NTNX_ACCOUNT_2_SUBNET_2_UUID not in env_str
        assert AWS_ACCOUNT_UUID in env_str
        assert VMWARE_ACCOUNT_UUID in env_str
        assert GCP_ACCOUNT_UUID in env_str

    def _test_create_environment(self):
        """
        Test creates a new enivoronment to existing project
        """

        runner = CliRunner()
        LOG.info("Creating Project using file at {}".format(DSL_PROJECT_PATH))
        result = runner.invoke(
            cli,
            [
                "create",
                "environment",
                "--file={}".format(DSL_ENVIRONMENT_PATH),
                "--name={}".format(ENV_3_NAME),
                "--project={}".format(self.project_name),
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
            pytest.fail("Environment create command failed")

        self.update_test_data()
        assert self.env3_uuid != "", "Environment '{}' not found".format(ENV_3_NAME)

        env_data = get_environment_by_uuid(self.env3_uuid)
        env_account_uuids = []

        for _obj in env_data["spec"]["resources"]["infra_inclusion_list"]:
            env_account_uuids.append(_obj["account_reference"]["uuid"])

        assert GCP_ACCOUNT_UUID in env_account_uuids
        assert VMWARE_ACCOUNT_UUID in env_account_uuids
        assert NTNX_ACCOUNT_1_UUID in env_account_uuids
        assert AWS_ACCOUNT_UUID in env_account_uuids

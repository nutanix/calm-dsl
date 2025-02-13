import pytest
from click.testing import CliRunner
from itertools import combinations
import uuid
import time
import sys
import json
import traceback
from distutils.version import LooseVersion as LV
from tests.utils import get_vpc_project
from tests.cli.test_utils import DelayedAssert
from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.cli.marketplace import (
    get_app_family_list,
    get_group_data_value,
    get_mpi_by_name_n_version,
)
from calm.dsl.cli.utils import get_states_filter
from calm.dsl.builtins import read_local_file
from calm.dsl.cli.constants import MARKETPLACE_ITEM
from calm.dsl.log import get_logging_handle
from tests.utils import Application as ApplicationHelper
from calm.dsl.store import Version
from tests.constants import PROVIDER, BP_SPEC

LOG = get_logging_handle(__name__)
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CALM_VERSION = Version.get_version("Calm")
CLUSTER = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]["SUBNETS"][1]["CLUSTER"]
APP_ICON_IMAGE_PATH = "tests/cli/images/test_app_icon.jpg"
DSL_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.py"
DSL_BP_WITH_OVERLAY_SUBNETS = (
    "tests/ahv_vm_overlay_subnet/test_overlay_subnet_blueprint.py"
)
DSL_BP_EDITABLE_PARAMS = "tests/existing_vm_example/existing_vm_bp_editable_params.py"
DSL_AHV_BP_FILEPATH = "tests/blueprint_example/test_ahv_bp/blueprint.py"
DSL_VMW_BP_FILEPATH = "tests/blueprint_example/test_vmware_bp/blueprint.py"
DSL_AWS_BP_FILEPATH = "tests/blueprint_example/test_aws_bp/blueprint.py"
DSL_AZURE_BP_FILEPATH = "tests/blueprint_example/test_azure_bp/blueprint.py"
DSL_GCP_BP_FILEPATH = "tests/blueprint_example/test_gcp_bp/blueprint.py"

APP_STATES = [
    MARKETPLACE_ITEM.STATES.PENDING,
    MARKETPLACE_ITEM.STATES.ACCEPTED,
    MARKETPLACE_ITEM.STATES.REJECTED,
    MARKETPLACE_ITEM.STATES.PUBLISHED,
]
APP_SOURCES = [
    MARKETPLACE_ITEM.SOURCES.GLOBAL,
    MARKETPLACE_ITEM.SOURCES.LOCAL,
]

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
# projects
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


class TestMarketplaceBPCommands:
    app_helper = ApplicationHelper()

    def setup_method(self):
        """Method to instantiate to created_bp_list and created_app_list"""

        self.created_bp_list = []
        self.created_app_list = []

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for app_name in self.created_app_list:
            LOG.info("Deleting app {}".format(app_name))
            self._test_app_delete(app_name)

        self.created_app_list = []
        self.created_bp_list = []

    def test_get_marketplace_items(self):
        """Tests 'calm get marketplace items command'"""

        runner = CliRunner()
        LOG.info("Running 'calm get marketplace items' command")
        result = runner.invoke(cli, ["get", "marketplace", "items"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace items")
        LOG.info("Success")

        # Test display all flag
        LOG.info("Running 'calm get marketplace items --display_all' command")
        result = runner.invoke(cli, ["get", "marketplace", "items", "--display_all"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace items with display_all flag")
        LOG.info("Success")

        # Test quiet flag
        LOG.info("Running 'calm get marketplace items --quiet' command")
        result = runner.invoke(cli, ["get", "marketplace", "items", "--quiet"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace items with quiet flag")
        LOG.info("Success")

        # Test app_family attribute
        LOG.info("Testing app_family option for  'calm get marketplace items' command")
        app_family_list = get_app_family_list()
        input = ["get", "marketplace", "items", "--app_family", ""]
        for app_family in app_family_list:
            input[4] = app_family
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.output)
                pytest.fail("Failed to fetch marketplace items with app_family option")
        LOG.info("Success")

        # Test filter attribute
        LOG.info("Running 'calm get marketplace items --filter' command")
        result = runner.invoke(
            cli, ["get", "marketplace", "items", "--filter", "version==1.0.0"]
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
            pytest.fail("Failed to fetch marketplace items with 'filter' cli option")
        LOG.info("Success")

    def test_get_marketplace_bps(self):
        """Tests 'calm get marketplace bps command'"""

        runner = CliRunner()

        LOG.info("Running 'calm get marketplace bps' command")
        result = runner.invoke(cli, ["get", "marketplace", "bps"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace bps")
        LOG.info("Success")

        # Test quiet flag
        LOG.info("Running 'calm get marketplace bps --quiet' command")
        result = runner.invoke(cli, ["get", "marketplace", "bps", "--quiet"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace bps with quiet flag")
        LOG.info("Success")

        # Test app states option
        LOG.info("Testing app_state option for  'calm get marketplace bps' command")
        app_states = APP_STATES
        app_states = sum(
            [
                list(map(list, combinations(app_states, i)))
                for i in range(len(app_states) + 1)
            ],
            [],
        )
        for app_state_list in app_states:
            input = ["get", "marketplace", "bps"]
            for app_state in app_state_list:
                input.append("--app_state")
                input.append(app_state)
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.ouput)
                pytest.fail("Failed to fetch marketplace bps with app_state option")
        LOG.info("Success")

        # Test app_family attribute
        LOG.info("Testing app_family option for  'calm get marketplace items' command")
        app_family_list = get_app_family_list()
        input = ["get", "marketplace", "items", "--app_family", ""]
        for app_family in app_family_list:
            input[4] = app_family
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.output)
                pytest.fail("Failed to fetch marketplace bps with app_family option")
        LOG.info("Success")

        # Test filter attribute
        LOG.info("Running 'calm get marketplace bps --filter' command")
        result = runner.invoke(
            cli, ["get", "marketplace", "bps", "--filter", "version==1.0.0"]
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
            pytest.fail("Failed to fetch marketplace bps with 'filter' cli option")
        LOG.info("Success")

    def test_describe_marketplace_item_with_default_version(self):

        payload = {
            "grouping_attribute": "app_group_uuid",
            "group_member_sort_attribute": "version",
            "group_member_sort_order": "DESCENDING",
            "group_count": 48,
            "group_member_count": 1,
            "group_offset": 0,
            "filter_criteria": "marketplace_item_type_list==APP;(app_state==PUBLISHED)",
            "entity_type": "marketplace_item",
            "group_member_attributes": [
                {"attribute": "name"},
                {"attribute": "version"},
            ],
        }

        client = get_api_client()
        Obj = get_resource_api("groups", client.connection)

        res, err = Obj.create(payload=payload)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        res = res.json()
        group_results = res["group_results"]
        if not group_results:
            pytest.skip("No marketplace item found.")

        group = group_results[0]
        entity_data = group["entity_results"][0]["data"]

        mpi_name = get_group_data_value(entity_data, "name")
        runner = CliRunner()

        LOG.info("Testing 'calm describe marketplace_item {}' command".format(mpi_name))
        result = runner.invoke(cli, ["describe", "marketplace", "item", mpi_name])
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
            pytest.fail("MPI list call failed")
        LOG.info("Success")

    def test_describe_marketplace_item_with_user_version(self):
        """To describe mpi with given version(cli input)"""

        payload = {
            "grouping_attribute": "app_group_uuid",
            "group_member_sort_attribute": "version",
            "group_member_sort_order": "DESCENDING",
            "group_count": 48,
            "group_member_count": 1,
            "group_offset": 0,
            "filter_criteria": "marketplace_item_type_list==APP;(app_state==PUBLISHED)",
            "entity_type": "marketplace_item",
            "group_member_attributes": [
                {"attribute": "name"},
                {"attribute": "version"},
            ],
        }

        client = get_api_client()
        Obj = get_resource_api("groups", client.connection)

        res, err = Obj.create(payload=payload)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        res = res.json()
        group_results = res["group_results"]
        if not group_results:
            pytest.skip("No marketplace item found.")

        group = group_results[0]
        entity_data = group["entity_results"][0]["data"]

        mpi_name = get_group_data_value(entity_data, "name")
        mpi_version = get_group_data_value(entity_data, "version")

        runner = CliRunner()

        LOG.info(
            "Testing 'calm describe marketplace_item {} --version {}' command".format(
                mpi_name, mpi_version
            )
        )
        result = runner.invoke(
            cli, ["describe", "marketplace", "item", mpi_name, "--version", mpi_version]
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
            pytest.fail("MPI list call failed")
        LOG.info("Success")

    def test_describe_marketplace_bp(self):
        """To describe marketplace blueprint"""

        payload = {"length": 250}

        client = get_api_client()
        runner = CliRunner()

        # test source option and app state action
        app_states = APP_STATES
        app_sources = APP_SOURCES

        LOG.info("Testing 'calm describe marketplace bp command'")
        for app_state in app_states:
            for app_source in app_sources:
                filter_query = ""
                if app_state:
                    filter_query += get_states_filter(
                        state_key="app_state", states=[app_state]
                    )

                if app_source:
                    filter_query += ";app_source=={}".format(app_source)

                if filter_query.startswith(";"):
                    filter_query = filter_query[1:]

                if filter_query:
                    payload["filter"] = filter_query

                res, err = client.market_place.list(params=payload)
                if err:
                    raise Exception("[{}] - {}".format(err["code"], err["error"]))

                res = res.json()
                total_matches = res["metadata"]["total_matches"]
                if not total_matches:
                    continue

                entity = res["entities"][0]
                mpi_name = entity["metadata"]["name"]
                mpi_version = entity["status"]["version"]

                command = [
                    "describe",
                    "marketplace",
                    "bp",
                    mpi_name,
                    "--version",
                    mpi_version,
                    "--app_state",
                    app_state,
                    "--source",
                    app_source,
                ]
                result = runner.invoke(cli, command)

                if result.exit_code:
                    cli_res_dict = {
                        "Output": result.output,
                        "Exception": str(result.exception),
                    }
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
                    pytest.fail("Describe marketplace blueprint command failed")

        LOG.info("Success")

    def _create_bp(self, BP_PATH=DSL_BP_FILEPATH, name=None):

        self.created_dsl_bp_name = name or "Test_Existing_VM_DSL_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info("Creating Bp {}".format(self.created_dsl_bp_name))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(BP_PATH),
                "--name={}".format(self.created_dsl_bp_name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )

        LOG.debug("Response: {}".format(result.output))
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
            pytest.fail("BP creation failed")

    @pytest.mark.parametrize(
        "BP_PATH",
        [
            pytest.param(DSL_BP_FILEPATH),
            pytest.param(
                DSL_BP_WITH_OVERLAY_SUBNETS,
                marks=pytest.mark.skipif(
                    LV(CALM_VERSION) < LV("3.5.0")
                    or not DSL_CONFIG.get("IS_VPC_ENABLED", False),
                    reason="VPC Tunnels can be used in Calm v3.5.0+ or VPC is disabled on the setup",
                ),
            ),
        ],
    )
    def test_mpi_basic_commands(self, BP_PATH):
        """
        Steps:
            1. Create a blueprint
            2. Publish this blueprint as new marketplace blueprint i.e. mp_bp1
            3. Publish the same blueprint as existing marketplace blueprint i.e. mp_bp2
            3. Publish the same blueprint with secrets as existing marketplace blueprint i.e. mp_bp3
            4. Negative Test: Publish the same blueprint with mp_bp2 's version
            5. Approve the mp_bp1
            6. Publish the mp_bp1
            7. Negative Test: Delete the published blueprint
            8. Unpublish the blueprint mp_bp1
            9. Delete the blueprint in ACCEPTED state i.e. mp_bp1
            10. Reject the blueprint i.e. mp_bp2
            11. Delete the blueprint in REJECTED state i.e. mp_bp2
            12. Delete the blueprint in PENDING sates i.e. mp_bp3

        """

        self._create_bp(BP_PATH)
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"
        self.mpi2_version = "2.0.0"
        self.mpi3_with_secrets_version = "3.0.0"

        # Publish Bp to marketplace manager as new marketplace blueprint
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of blueprint as new marketplace item failed")
        LOG.info("Success")

        LOG.info(
            "Publishing Bp {} as existing marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi2_version,
            "--name",
            self.marketplace_bp_name,
            "--existing_marketplace_bp",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of blueprint as existing marketplace_item failed")
        LOG.info("Success")

        LOG.info(
            "Publishing Bp {} with secrets as existing marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi3_with_secrets_version,
            "--name",
            self.marketplace_bp_name,
            "--existing_marketplace_bp",
            "--with_secrets",
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Publishing of blueprint with secrets as existing marketplace_item failed"
            )
        LOG.info("Success")

        LOG.info(
            "Negative Test: Publishing Bp {} as existing marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi2_version,
            "--name",
            self.marketplace_bp_name,
            "--existing_marketplace_bp",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code == 0:
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
            pytest.fail(
                "Publishing bp with version that already exists in marketplace should not be successful"
            )
        LOG.info("Success")

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Approving of marketplace blueprint failed")
        LOG.info("Success")

        # Update the blueprint
        LOG.info(
            "Updating marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "update",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--description",
            "Sample description",
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Updating of marketplace blueprint failed")
        LOG.info("Success")

        # Publising blueprint without projects
        LOG.info(
            "Negative Test: Publishing marketplace blueprint {} with version {} to marketplace without projects".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code == 0:
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
            pytest.fail(
                "Publishing of marketplace blueprint without projects should fail"
            )
        LOG.info("Success")

        # Publishing marketplace blueprint
        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            PROJECT_NAME,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        # Try to delete the published blueprint
        LOG.info("Negative Test: Deleting marketplace blueprint in PUBLISHED state")
        command = [
            "delete",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code == 0:
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
            pytest.fail(
                "Deleting  of marketplace blueprint should fail if bp is in published state"
            )
        LOG.info("Success")

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Unpublishing of marketplace blueprint failed")
        LOG.info("Success")

        # Deleting the Accepted marketplace blueprint
        LOG.info(
            "Deleting marketplace blueprint {} with version {} in ACCEPTED state".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Deletion of marketplace blueprint in ACCEPTED state failed")
        LOG.info("Success")

        # Reject the marketplace blueprint
        LOG.info(
            "Rejecting marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi2_version
            )
        )
        command = [
            "reject",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi2_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Rejection of marketplace blueprint failed")
        LOG.info("Success")

        # Delete the rejected blueprint
        LOG.info("Deleting marketplace blueprint in REJECTED state")
        command = [
            "delete",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi2_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Deletion of marketplace blueprint in REJECTED state failed")
        LOG.info("Success")

        # Delete the pending blueprint
        LOG.info("Deleting marketplace blueprint in PENDING state")
        command = [
            "delete",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi3_with_secrets_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Deletion of marketplace blueprint in PENDING state failed")
        LOG.info("Success")

    @pytest.mark.slow
    @pytest.mark.parametrize(
        "BP_PATH",
        [
            pytest.param(DSL_BP_FILEPATH),
            pytest.param(
                DSL_BP_WITH_OVERLAY_SUBNETS,
                marks=pytest.mark.skipif(
                    LV(CALM_VERSION) < LV("3.5.0")
                    or not DSL_CONFIG.get("IS_VPC_ENABLED", False),
                    reason="VPC Tunnels can be used in Calm v3.5.0+ or VPC is disabled on the setup",
                ),
            ),
        ],
    )
    def test_mpi_launch(self, BP_PATH):
        """
        Steps:
            1. Create a blueprint
            2. Publish the blueprint to marketplace manager
            3. Launch the blueprint in PENDING state and delete the app
            4. Approve the blueprint
            5. Launch the blueprint in ACCEPTED state and delete the app
            6. Publish the blueprint in marketplace
            7. Launch the mpi and delete the app
            8. Delete the blueprint
        """

        self._create_bp(BP_PATH)
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp to marketplace manager as new marketplace blueprint
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--with_secrets",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Publishing of marketplace blueprint as new marketplace item failed"
            )
        LOG.info("Success")

        # Launch the bp in PENDING state
        self.pending_mpbp_app_name = "Test_MPI_APP_{}".format(str(uuid.uuid4())[-10:])
        LOG.info(
            "Launch Bp {} with version {} in PENDING state".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        if BP_PATH == DSL_BP_WITH_OVERLAY_SUBNETS:
            profile_name = "HelloProfile"
            proj_name = get_vpc_project(DSL_CONFIG)["name"]
        else:
            profile_name = "DefaultProfile"
            proj_name = PROJECT_NAME

        command = [
            "launch",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
            "--app_name",
            self.pending_mpbp_app_name,
            "--profile_name",
            profile_name,
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in PENDING state failed")
        self.created_app_list.append(self.pending_mpbp_app_name)

        # Launch the bp in PENDING state using launch_params
        self.pending_mpbp_lp_app_name = "Test_MPI_APP_LP_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info(
            "Launch Bp {} with version {} in PENDING state with launch_params".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "launch",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
            "--app_name",
            self.pending_mpbp_lp_app_name,
            "--profile_name",
            profile_name,
            "--launch_params",
            DSL_BP_EDITABLE_PARAMS,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Launching of marketplace blueprint in PENDING state  with launch_params failed"
            )
        self.created_app_list.append(self.pending_mpbp_lp_app_name)

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Approving of marketplace blueprint failed")
        LOG.info("Success")

        # Launching the bp in ACCEPTED state
        self.accepted_mpbp_app_name = "Test_MPI_APP_{}".format(str(uuid.uuid4())[-10:])
        LOG.info(
            "Launch Bp {} with version {} in ACCEPTED state".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "launch",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
            "--app_name",
            self.accepted_mpbp_app_name,
            "--profile_name",
            profile_name,
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in ACCEPTED state failed")
        self.created_app_list.append(self.accepted_mpbp_app_name)

        # Publish blueprint to marketplace
        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        # Launching the bp in PUBLISHED state(Marketplace Item)
        self.published_mpbp_app_name = "Test_MPI_APP_{}".format(str(uuid.uuid4())[-10:])
        LOG.info(
            "Launching Marketplace Item {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "launch",
            "marketplace",
            "item",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
            "--app_name",
            self.published_mpbp_app_name,
            "--profile_name",
            profile_name,
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in PUBLISHED state failed")
        self.created_app_list.append(self.published_mpbp_app_name)

        # Launching the bp in PUBLISHED state(Marketplace Item) with launch_params
        self.published_mpbp_lp_app_name = "Test_MPI_APP_LP_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info(
            "Launching Marketplace Item {} with version {} with launch_params".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "launch",
            "marketplace",
            "item",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
            "--app_name",
            self.published_mpbp_lp_app_name,
            "--profile_name",
            profile_name,
            "--launch_params",
            DSL_BP_EDITABLE_PARAMS,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in PUBLISHED state failed")
        self.created_app_list.append(self.published_mpbp_lp_app_name)

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Unpublishing of marketplace blueprint in PUBLISHED state failed"
            )
        LOG.info("Success")

        self._delete_mpi()

    @pytest.mark.slow
    @pytest.mark.skipif(
        LV(CALM_VERSION) < LV("3.8.0"),
        reason="MPI without Platform dependant fields was released in 3.8.0 hence cannot be tested on lower versions",
    )
    @pytest.mark.parametrize(
        "provider, BP_PATH",
        [
            ("AHV", DSL_AHV_BP_FILEPATH),
            ("VMW", DSL_VMW_BP_FILEPATH),
            ("AWS", DSL_AWS_BP_FILEPATH),
            ("GCP", DSL_GCP_BP_FILEPATH),
            ("AZURE", DSL_AZURE_BP_FILEPATH),
        ],
    )
    def test_mpi_launch_without_platfrom_dependant_fields(self, provider, BP_PATH):
        """
        Metadata:
            Summary: This test verifies launching of marketplace blueprint without platform_dependant_fields
            Priority: $P0
            Steps:
                - 1. Create a blueprint
                - 2. Publish the blueprint to marketplace manager
                - 3. Launch the blueprint in PENDING state and delete the app
                - 4. Approve the blueprint
                - 5. Launch the blueprint in ACCEPTED state and delete the app
                - 6. Publish the blueprint in marketplace
                - 7. Launch the mpi and delete the app
                - 8. Delete the blueprint
                - ExpectedResults
                    - Publish the blueprint to marketplace manager without platform_dependant_fields should be successful
                    - Launching of marketplace blueprint without platform_dependant_fields should be successful

        """
        # Create a blueprint

        proj_name = BP_SPEC.PROJECT_NAME_DEFAULT
        self._create_bp(BP_PATH)
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish the blueprint to marketplace manager without platform_dependant_fields

        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--without-platform-data",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Publishing of marketplace blueprint as new marketplace item failed"
            )
        LOG.info("Success")

        # Approve the blueprint

        LOG.info(
            "Approving marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Approving of marketplace blueprint failed")
        LOG.info("Success")

        # Publish the blueprint to marketplace

        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        # Verify MPI published is blank for platform_dependant_fields

        LOG.info(
            "Verifying Marketplace Item {} with version {} is published without platform dependent feilds".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "describe",
            "marketplace",
            "item",
            self.marketplace_bp_name,
            "--out=json",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Describe of marketplace blueprint in PUBLISHED state failed")

        self._verify_platform_dependent_fields_mpi(provider, result.output)

        # Launching the bp in PUBLISHED state(Marketplace Item)
        self.published_mpbp_app_name = "Test_MPI_APP_{}".format(str(uuid.uuid4())[-10:])
        LOG.info(
            "Launching Marketplace Item {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )

        command = [
            "launch",
            "marketplace",
            "item",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            proj_name,
            "--app_name",
            self.published_mpbp_app_name,
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in PUBLISHED state failed")
        self.created_app_list.append(self.published_mpbp_app_name)

        # verify mpi patching from environment
        command = [
            "describe",
            "app",
            self.published_mpbp_app_name,
            "--out=json",
        ]
        runner = CliRunner()
        result = runner.invoke(cli, command)
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
            pytest.fail("Describe of marketplace app in PUBLISHED state failed")

        self._verify_platform_dependent_fields_app(provider, result.output)
        LOG.info("Success")

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Unpublishing of marketplace blueprint in PUBLISHED state failed"
            )
        LOG.info("Success")

        self._delete_mpi()

    def _verify_platform_dependent_fields_mpi(self, provider, result):
        """
        Verifies platform-dependent fields in the marketplace blueprint configuration.

        This function checks the presence of specific fields in the marketplace
        blueprint configuration based on the provider type. It asserts that the expected
        fields are present in the result string.

        Args:
            provider (str): The provider type (e.g., "AHV", "VMW").
            result (str): The JSON string containing the marketplace blueprint configuration.

        Raises:
            AssertionError: If any of the expected fields are not found in the result.
        """
        expect = DelayedAssert()
        result = json.loads(result)
        if provider == "AHV":
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nic_list"][0]["subnet_reference"]
                == {}
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["categories"]
                == {}
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["cluster_reference"]
                == {}
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["disk_list"][0]["data_source_reference"]
                == {}
            )

        elif provider == "VMW":
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nic_list"][0]["net_name"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nic_list"][0]["nic_type"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["tag_list"][0]["tag_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["template_nic_list"]
                == []
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["template_disk_list"]
                == []
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["template_controller_list"]
                == []
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["datastore"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["template"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["host"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["cluster"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["storage_pod"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["storage_drs_mode"]
                is None
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["compute_drs_mode"]
                is None
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["library"]
                is None
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["compute_drs_mode"]
                is None
            )

        elif provider == "AWS":
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["security_group_list"][0]["security_group_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["image_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["key_name"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["region"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["instance_profile_name"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["subnet_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["vpc_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["availability_zone_reference"]
                is None
            )

        elif provider == "GCP":
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["disks"][0]["source"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["disks"][0]["initializeParams"]["sourceImage"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["networkInterfaces"][0]["network"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["networkInterfaces"][0]["subnetwork"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["serviceAccounts"][0]["email"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["tags"]["items"]
                == []
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["machineType"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["zone"]
                == ""
            )

        elif provider == "AZURE":
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["storage_profile"]["image_details"]["publisher"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["storage_profile"]["image_details"]["offer"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["storage_profile"]["image_details"]["sku"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["storage_profile"]["image_details"]["version"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["storage_profile"]["image_details"]["source_image_type"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["storage_profile"]["image_details"]["source_image_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["nsg_name"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["vnet_name"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["subnet_name"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["nsg_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["vnet_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["subnet_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["nw_profile"]["nic_list"][0]["asg_list"]
                == []
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["resource_group"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["location"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["availability_set_id"]
                == ""
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["rg_details"]
                == {}
            )
            expect.expect(
                result["spec"]["resources"]["substrate_definition_list"][0][
                    "create_spec"
                ]["resources"]["rg_operation"]
                == ""
            )

        expect.assert_expectations()

    def _verify_platform_dependent_fields_app(self, provider, result):
        """
        Verifies platform-dependent fields in the application configuration.

        This function checks the presence of specific fields in the application
        configuration based on the provider type. It asserts that the expected
        fields are present in the result string.

        Args:
            provider (str): The provider type (e.g., "AHV", "VMW").
            result (str): The JSON string containing the application configuration.

        Raises:
            AssertionError: If any of the expected fields are not found in the result.
        """
        if provider == "AHV":
            assert PROVIDER.AHV.NIC in result
            assert PROVIDER.AHV.LINIX_IMAGE in result

        elif provider == "VMW":
            expected_substrings = [
                PROVIDER.VMWARE.DND_CENTOS_WITH_NIC_J_TEMPLATE,
                PROVIDER.VMWARE.DATASTORE,
                PROVIDER.VMWARE.HOST,
                PROVIDER.VMWARE.TAG_ID,
                PROVIDER.VMWARE.VNIC.NET_NAME_API,
                PROVIDER.VMWARE.VNIC.NIC_TYPE_API,
                PROVIDER.VMWARE.SCSI_CONTROLLER.CONTROLLER_TYPE_API,
            ]
            for substring in expected_substrings:
                assert substring in result

        elif provider == "AWS":
            expected_substrings = [
                PROVIDER.AWS.SECGROUPID,
                PROVIDER.AWS.AMIID,
                PROVIDER.AWS.DEFAULT_KEYNAME,
                PROVIDER.AWS.DEFAULT_REGION,
                PROVIDER.AWS.DEFAULT_PROFILE,
                PROVIDER.AWS.DEFAULT_SUBNET,
                PROVIDER.AWS.DEFAULT_VPC,
            ]
            for substring in expected_substrings:
                assert substring in result

        elif provider == "GCP":
            expected_substrings = [
                PROVIDER.GCP.SOURCE_IMAGE,
                PROVIDER.GCP.NETWORK_NAME,
                PROVIDER.GCP.SUBNETWORK_NAME,
                PROVIDER.GCP.CLIENT_EMAIL,
                PROVIDER.GCP.ITEMS,
                PROVIDER.GCP.MACHINE_TYPE,
                PROVIDER.GCP.DEFAULT_ZONE,
            ]
            for substring in expected_substrings:
                assert substring in result

        elif provider == "AZURE":
            expected_substrings = [
                PROVIDER.AZURE.PUBLIC_IMAGE_PUBLISHER,
                PROVIDER.AZURE.PUBLIC_IMAGE_OFFER,
                PROVIDER.AZURE.PUBLIC_IMAGE_SKU,
                PROVIDER.AZURE.PUBLIC_IMAGE_VERSION,
                PROVIDER.AZURE.IMAGE_MARKETPLACE,
                PROVIDER.AZURE.SECURITY_GROUP,
                PROVIDER.AZURE.VIRTUAL_NETWORK,
                PROVIDER.AZURE.SUBNET_NAME,
                PROVIDER.AZURE.RESOURCE_GROUP,
                PROVIDER.AZURE.RG_OPERATION,
                PROVIDER.AZURE.NSG_ID,
                PROVIDER.AZURE.VNET_ID,
                PROVIDER.AZURE.SUBNET_ID,
            ]
            for substring in expected_substrings:
                assert substring in result

    def test_publish_to_marketplace_flag(self):
        """Test for publish_to_marketplace_flag for publsh command"""

        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp directly to marketplace using --publish_to_marketplace flag
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--publish_to_marketplace",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing Bp using publish_to_marketplace flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )
        bp_state = mpi_data["status"]["resources"]["app_state"]
        assert bp_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Unpublishing of marketplace blueprint failed")

        self._delete_mpi()

    def test_auto_approve_flag(self):
        """Test for auto_approve flag in publish command"""

        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--auto_approve",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing Bp using auto_approve flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )
        bp_state = mpi_data["status"]["resources"]["app_state"]
        assert bp_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        self._delete_mpi()

    def test_publish_bp_with_icon(self):
        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)

        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"
        self.icon_name = "test_icon{}".format(str(uuid.uuid4())[:10])

        LOG.info("Publishing the blueprint to marketplace manager")
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "-f",
            APP_ICON_IMAGE_PATH,
            "-i",
            self.icon_name,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of blueprint as new marketplace item failed")
        LOG.info("Success")

        client = get_api_client()
        app_icon_name_uuid_map = client.app_icon.get_name_uuid_map()
        app_icon_uuid = app_icon_name_uuid_map.get(self.icon_name)

        bp_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name, version=self.mpi1_version
        )
        icon_reference = bp_data["status"]["resources"]["icon_reference_list"][0][
            "icon_reference"
        ]
        assert icon_reference["uuid"] == app_icon_uuid, "App icon not used for the bp"

        self._delete_mpi()

    def test_all_projects_flag_on_publising_bp_with_auto_approve_flag(self):
        """Tests `--all_projects` flag to publish bp to marketplace manager with auto approval flag"""

        client = get_api_client()
        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp marketplace using --all_projects flag
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {} with 'all_projects' flag".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--all_projects",
            "--auto_approve",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing Bp using all_projects flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        bp_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            bp_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in bp_projects

        self._delete_mpi()

    def test_all_projects_flag_on_approving_marketplace_bp(self):
        """Tests `--all_projects` flag to approving bp to marketplace manager"""

        client = get_api_client()
        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp to marketplace manager as new marketplace blueprint
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--with_secrets",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Publishing of marketplace blueprint as new marketplace item failed"
            )

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {} with 'all_projects' flag".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--all_projects",
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Approving of marketplace blueprint using all_projects flag failed"
            )
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        bp_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            bp_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in bp_projects

        self._delete_mpi()

    def test_all_projects_flag_on_publishing_marketplace_bp(self):
        """Tests `--all_projects` flag for publishing bp to marketplace store"""

        client = get_api_client()
        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp directly to marketplace using --auto_approve flag
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--auto_approve",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing Bp using auto_approve flag failed")
        LOG.info("Success")

        # Publish blueprint to marketplace
        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace with 'all_projects' flag".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--all_projects",
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        bp_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            bp_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in bp_projects

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Unpublishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        self._delete_mpi()

    def _test_app_delete(self, app_name):

        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Deleting App {} ".format(app_name))
        result = runner.invoke(cli, ["delete", "app", app_name])
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
            pytest.fail("Deletion of application '{}' failed".format(app_name))
        LOG.info("App is deleted successfully")

    def _delete_mpi(self):
        runner = CliRunner()
        LOG.info(
            "Deleting marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Deletion of marketplace blueprint failed")

        LOG.info("Success")

    def test_all_projects_flag_on_publising_bp_without_auto_approve_flag(self):
        """Tests `--all_projects` flag to publish bp to marketplace manager without auto approval flag"""

        client = get_api_client()
        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp marketplace using --all_projects flag
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {} with 'all_projects' flag".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--all_projects",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing Bp using all_projects flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        bp_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            bp_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in bp_projects

        self._delete_mpi()

    def test_project_removal_flag_on_approving_marketplace_bp(self):
        """Tests `--remove-project` flag on approving bp to marketplace manager"""

        project_name = "default"  # This project will be removed while approving
        self._create_bp()
        self.created_bp_list.append(self.created_dsl_bp_name)
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp to marketplace manager as new marketplace blueprint with all projects
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            self.created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
            "--all_projects",
            "--with_secrets",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Publishing of marketplace blueprint as new marketplace item failed"
            )

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {} and removing {} project".format(
                self.marketplace_bp_name, self.mpi1_version, project_name
            )
        )
        command = [
            "approve",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--remove-project",
            project_name,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Approving of marketplace blueprint using remove-project flag failed"
            )
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_bp_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        bp_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            bp_projects.append(_proj["name"])

        assert project_name not in bp_projects

        self._delete_mpi()

import pytest
from click.testing import CliRunner
from itertools import combinations
import uuid
import time

from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.cli.mpis import get_app_family_list, get_group_data_value
from calm.dsl.cli.utils import get_states_filter
from calm.dsl.cli.constants import APPLICATION
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.py"
NON_BUSY_APP_STATES = [
    APPLICATION.STATES.STOPPED,
    APPLICATION.STATES.RUNNING,
    APPLICATION.STATES.ERROR,
]


@pytest.mark.slow
class TestMPICommands:
    def test_get_marketplace_items(self):
        """Tests 'calm get marketplace_items command'"""

        runner = CliRunner()
        LOG.info("Running 'calm get marketplace_items' command")
        result = runner.invoke(cli, ["get", "marketplace_items"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("MPI list call failed")
        LOG.info("Success")

        # Test display all flag
        LOG.info("Running 'calm get marketplace_items --display_all' command")
        result = runner.invoke(cli, ["get", "marketplace_items", "--display_all"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("MPI list call with display_all flag failed")
        LOG.info("Success")

        # Test quiet flag
        LOG.info("Running 'calm get marketplace_items --quiet' command")
        result = runner.invoke(cli, ["get", "marketplace_items", "--quiet"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("MPI list call with quiet flag failed")
        LOG.info("Success")

        # Test app_family attribute
        LOG.info("Testing app_family option for  'calm get marketplace_items' command")
        app_family_list = get_app_family_list()
        input = ["get", "marketplace_items", "--app_family", ""]
        for app_family in app_family_list:
            input[3] = app_family
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.output)
                pytest.fail("MPI list call with app_family option failed")
        LOG.info("Success")

    def test_get_marketplace_bps(self):
        """Tests 'calm get marketplace_bps command'"""

        runner = CliRunner()

        LOG.info("Running 'calm get marketplace_bps' command")
        result = runner.invoke(cli, ["get", "marketplace_bps"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("MPI list call failed")
        LOG.info("Success")

        # Test quiet flag
        LOG.info("Running 'calm get marketplace_bps --quiet' command")
        result = runner.invoke(cli, ["get", "marketplace_bps", "--quiet"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("MPI list call with quiet flag failed")
        LOG.info("Success")

        # Test app states option
        LOG.info("Testing app_state option for  'calm get marketplace_bps' command")
        app_states = ["REJECTED", "ACCEPTED", "PUBLISHED", "PENDING"]
        app_states = sum(
            [
                list(map(list, combinations(app_states, i)))
                for i in range(len(app_states) + 1)
            ],
            [],
        )
        for app_state_list in app_states:
            input = ["get", "marketplace_bps"]
            for app_state in app_state_list:
                input.append("--app_state")
                input.append(app_state)
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.ouput)
                pytest.fail("MPI list call with app_state option failed")
        LOG.info("Success")

        # Test app_family attribute
        LOG.info("Testing app_family option for  'calm get marketplace_items' command")
        app_family_list = get_app_family_list()
        input = ["get", "marketplace_items", "--app_family", ""]
        for app_family in app_family_list:
            input[3] = app_family
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.output)
                pytest.fail("MPI list call with app_family option failed")
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
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        group = res["group_results"][0]
        entity_data = group["entity_results"][0]["data"]

        mpi_name = get_group_data_value(entity_data, "name")
        runner = CliRunner()

        LOG.info("Testing 'calm describe marketplace_item {}' command".format(mpi_name))
        result = runner.invoke(cli, ["describe", "marketplace_item", mpi_name])
        if result.exit_code:
            LOG.error(result.output)
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
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        group = res["group_results"][0]
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
            cli, ["describe", "marketplace_item", mpi_name, "--version", mpi_version]
        )
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("MPI list call failed")
        LOG.info("Success")

    def test_describe_marketplace_bp(self):
        """To describe marketplace blueprint"""

        payload = {"length": 250}

        client = get_api_client()
        runner = CliRunner()

        # test source option and app state action
        app_states = ["PENDING", "ACCEPTED", "REJECTED", "PUBLISHED", None]
        app_sources = ["GLOBAL_STORE", "LOCAL", None]

        LOG.info("Testing 'calm describe marketplace_bp command'")
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
                    "marketplace_bp",
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
                    LOG.error(result.output)
                    pytest.fail("Describe marketplace blueprint command failed")

        LOG.info("Success")

    def _create_bp(self):
        self.created_dsl_bp_name = "Test_Existing_VM_DSL_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info("Creating Bp {}".format(self.created_dsl_bp_name))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(self.created_dsl_bp_name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )

        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response: {}".format(result.output))

    def test_mpi_basic_commands(self):
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

        self._create_bp()
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
            LOG.error(result.output)
            pytest.fail(
                "Publishing of marketplace blueprint as new marketplace item failed"
            )
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
            "--existing_markeplace_bp",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail(
                "Publishing of marketplace blueprint as existing marketplace_item failed"
            )
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
            "--existing_markeplace_bp",
            "--with_secrets",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail(
                "Publishing of marketplace blueprint with secrets as existing marketplace_item failed"
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
            "--existing_markeplace_bp",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code == 0:
            LOG.error(result.output)
            pytest.fail(
                "Publishing bp with version that already exists in marketplace should not be successful"
            )
        LOG.info("Success")

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "approve",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Approving of marketplace blueprint failed")
        LOG.info("Success")

        # Update the blueprint
        LOG.info(
            "Updating marketplace blueprint {} with version {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "update",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--description",
            "Sample description",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Updating of marketplace blueprint failed")
        LOG.info("Success")

        # Publising blueprint without projects
        LOG.info(
            "Negative Test: Publishing marketplace blueprint {} with version {} to marketplace without projects".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code == 0:
            LOG.error(result.output)
            pytest.fail(
                "Publishing of marketplace blueprint without projects should fail"
            )
        LOG.info("Success")

        # Publishing marketplace blueprint
        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            "default",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Publishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        # Try to delete the published blueprint
        LOG.info("Negative Test: Deleting marketplace blueprint in PUBLISHED state")
        command = [
            "delete",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code == 0:
            LOG.error(result.output)
            pytest.fail(
                "Deleting  of marketplace blueprint should fail if bp is in published state"
            )
        LOG.info("Success")

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "unpublish",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Unpublishing of marketplace blueprint failed")
        LOG.info("Success")

        # Deleting the Accepted marketplace blueprint
        LOG.info("Deleting marketplace blueprint in ACCEPTED state")
        command = [
            "delete",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
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
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi2_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Rejection of marketplace blueprint failed")
        LOG.info("Success")

        # Delete the rejected blueprint
        LOG.info("Deleting marketplace blueprint in REJECTED state")
        command = [
            "delete",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi2_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Deletion of marketplace blueprint in REJECTED state failed")
        LOG.info("Success")

        # Delete the pending blueprint
        LOG.info("Deleting marketplace blueprint in PENDING state")
        command = [
            "delete",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi3_with_secrets_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Deletion of marketplace blueprint in PENDING state failed")
        LOG.info("Success")

        # Delete the blueprint
        LOG.info("Deleting DSL Bp {} ".format(self.created_dsl_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_dsl_bp_name])

        assert result.exit_code == 0
        LOG.info("Success")

    def test_mpi_launch(self):
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

        self._create_bp()
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
            LOG.error(result.output)
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
        command = [
            "launch",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            "default",
            "--app_name",
            self.pending_mpbp_app_name,
            "--profile_name",
            "DefaultProfile",
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Launching of marketplace blueprint in PENDING state failed")
        LOG.info("Success")

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
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
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            "default",
            "--app_name",
            self.accepted_mpbp_app_name,
            "--profile_name",
            "DefaultProfile",
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Launching of marketplace blueprint in ACCEPTED state failed")
        LOG.info("Success")

        # Publish blueprint to marketplace
        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            "default",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
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
            "marketplace_item",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            "default",
            "--app_name",
            self.published_mpbp_app_name,
            "--profile_name",
            "DefaultProfile",
            "-i",
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Launching of marketplace blueprint in PUBLISHED state failed")
        LOG.info("Success")

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        assert result.exit_code == 0
        LOG.info("Success")

        # Delete the marketplace blueprint
        LOG.info(
            "Deleting marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace_bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
        assert result.exit_code == 0
        LOG.info("Success")

        # Delete the blueprint
        LOG.info("Deleting DSL Bp {} ".format(self.created_dsl_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_dsl_bp_name])
        assert result.exit_code == 0

        # Deleting created apps
        self._test_app_delete(self.pending_mpbp_app_name)
        self._test_app_delete(self.accepted_mpbp_app_name)
        self._test_app_delete(self.published_mpbp_app_name)

    def _wait_for_non_busy_state(self, app_name):

        runner = CliRunner()
        non_busy_statuses = [
            "Status: {}".format(state) for state in NON_BUSY_APP_STATES
        ]
        result = runner.invoke(cli, ["describe", "app", app_name])
        while not any([state_str in result.output for state_str in non_busy_statuses]):
            time.sleep(5)
            result = runner.invoke(cli, ["describe", "app", app_name])

    def _test_app_delete(self, app_name):

        runner = CliRunner()
        self._wait_for_non_busy_state(app_name)
        LOG.info("Deleting App {} ".format(app_name))
        result = runner.invoke(cli, ["delete", "app", app_name])
        assert result.exit_code == 0
        LOG.info("App is deleted successfully")

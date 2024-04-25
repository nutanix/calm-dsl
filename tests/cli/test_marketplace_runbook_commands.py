import pytest
from click.testing import CliRunner
from itertools import combinations
import uuid
import json
import traceback
from distutils.version import LooseVersion as LV
from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client
from calm.dsl.cli.marketplace import (
    get_app_family_list,
    get_mpi_by_name_n_version,
)
from calm.dsl.cli.utils import get_states_filter
from calm.dsl.builtins import read_local_file
from calm.dsl.cli.constants import MARKETPLACE_ITEM
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version

LOG = get_logging_handle(__name__)
CALM_VERSION = Version.get_version("Calm")
APP_ICON_IMAGE_PATH = "tests/cli/images/test_app_icon.jpg"
DSL_RB_FILEPATH = "tests/sample_runbooks/simple_runbook.py"

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

PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


class TestMarketplaceRunbookCommands:
    def setup_method(self):
        """Method to instantiate to created_rb_list"""

        self.created_rb_list = []

    def teardown_method(self):
        """Method to delete creates runbooks during tests"""

        for rb_name in self.created_rb_list:
            LOG.info("Deleting Runbook {}".format(rb_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "runbook", rb_name])
            assert result.exit_code == 0

        self.created_rb_list = []

    def _create_runbook(self, RB_PATH):

        self.created_dsl_rb_name = "Test_Runbook_for_MPI_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info("Creating Runbook {}".format(self.created_dsl_rb_name))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "runbook",
                "--file={}".format(RB_PATH),
                "--name={}".format(self.created_dsl_rb_name),
                "--description='Test DSL Runbook; to delete'",
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
            pytest.fail("Runbook creation failed")

        LOG.info("Success")

    def _delete_mpi(self):
        runner = CliRunner()
        LOG.info(
            "Deleting marketplace runboook {} with version {}".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Deletion of marketplace runboook failed")
        LOG.info("Success")

    def test_get_marketplace_runbooks(self):
        """Tests 'calm get marketplace runbooks command'"""

        runner = CliRunner()

        LOG.info("Running 'calm get marketplace runbooks' command")
        result = runner.invoke(cli, ["get", "marketplace", "runbooks"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace runboooks")
        LOG.info("Success")

        # Test quiet flag
        LOG.info("Running 'calm get marketplace runbooks --quiet' command")
        result = runner.invoke(cli, ["get", "marketplace", "bps", "--quiet"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Failed to fetch marketplace runbooks with quiet flag")
        LOG.info("Success")

        # Test app states option
        LOG.info(
            "Testing app_state option for  'calm get marketplace runbooks' command"
        )
        app_states = APP_STATES
        app_states = sum(
            [
                list(map(list, combinations(app_states, i)))
                for i in range(len(app_states) + 1)
            ],
            [],
        )
        for app_state_list in app_states:
            input = ["get", "marketplace", "runbooks"]
            for app_state in app_state_list:
                input.append("--app_state")
                input.append(app_state)
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.ouput)
                pytest.fail(
                    "Failed to fetch marketplace runbooks with app_state option"
                )
        LOG.info("Success")

        # Test app_family attribute
        LOG.info(
            "Testing app_family option for  'calm get marketplace runbooks' command"
        )
        app_family_list = get_app_family_list()
        input = ["get", "marketplace", "runbooks", "--app_family", ""]
        for app_family in app_family_list:
            input[4] = app_family
            result = runner.invoke(cli, input)
            if result.exit_code:
                LOG.error(result.output)
                pytest.fail(
                    "Failed to fetch marketplace runbooks with app_family option"
                )
        LOG.info("Success")

        # Test filter attribute
        LOG.info("Running 'calm get marketplace runbooks --filter' command")
        result = runner.invoke(
            cli, ["get", "marketplace", "runbooks", "--filter", "version==1.0.0"]
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
            pytest.fail("Failed to fetch marketplace runbooks with 'filter' cli option")
        LOG.info("Success")

    def test_describe_marketplace_runbook(self):
        """To describe marketplace runbook"""

        payload = {"length": 250}

        client = get_api_client()
        runner = CliRunner()

        # test source option and app state action
        app_states = APP_STATES
        app_sources = APP_SOURCES

        LOG.info("Testing 'calm describe marketplace runbook command'")
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
                    "runbook",
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
                    pytest.fail("Describe marketplace runbook command failed")

        LOG.info("Success")

    def test_mpi_basic_commands(self):
        """
        Steps:
            1. Create a runbook
            2. Publish this runbook as new marketplace runbook i.e. mp_rb1
            3. Publish the same runbook as existing marketplace runbook i.e. mp_rb2
            3. Publish the same runbook with secrets as existing marketplace runbook i.e. mp_rb3
            4. Negative Test: Publish the same runbook with mp_rb2 's version
            5. Approve the mp_rb1
            6. Publish the mp_rb1
            7. Negative Test: Delete the published runbook
            8. Unpublish the runbook mp_rb1
            9. Delete the runbook in ACCEPTED state i.e. mp_rb1
            10. Reject the runbook i.e. mp_rb2
            11. Delete the runbook in REJECTED state i.e. mp_rb2
            12. Delete the runbook in PENDING sates i.e. mp_rb3

        """

        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Runbook_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"
        self.mpi2_version = "2.0.0"
        self.mpi3_with_secrets_version = "3.0.0"

        # Publish Runbook to marketplace manager as new marketplace runbook
        LOG.info(
            "Publishing Rb {} as new marketplace Runbook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing of Runbook as new marketplace item failed")
        LOG.info("Success")

        LOG.info(
            "Publishing Runbook {} as existing marketplace runbook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi2_version,
            "--name",
            self.marketplace_rb_name,
            "--existing_marketplace_runbook",
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
            pytest.fail("Publishing of runbook as existing marketplace_item failed")
        LOG.info("Success")

        LOG.info(
            "Publishing Runboook {} with secrets as existing marketplace runbook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi3_with_secrets_version,
            "--name",
            self.marketplace_rb_name,
            "--existing_marketplace_runbook",
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
                "Publishing of runbook with secrets as existing marketplace_item failed"
            )
        LOG.info("Success")

        LOG.info(
            "Negative Test: Publishing runbook {} as existing marketplace runbook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi2_version,
            "--name",
            self.marketplace_rb_name,
            "--existing_markeplace_runbook",
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
                "Publishing runbook with version that already exists in marketplace should not be successful"
            )
        LOG.info("Success")

        # Approve the runbook
        LOG.info(
            "Approving marketplace runbook {} with version {}".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Approving of marketplace runbook failed")
        LOG.info("Success")

        # Update the runbook
        LOG.info(
            "Updating marketplace runbook {} with version {}".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "update",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Updating of marketplace runbook failed")
        LOG.info("Success")

        # Publising runboook without projects
        LOG.info(
            "Negative Test: Publishing marketplace runbook {} with version {} to marketplace without projects".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
                "Publishing of marketplace runbook without projects should fail"
            )
        LOG.info("Success")

        # Publishing marketplace runbook
        LOG.info(
            "Publishing marketplace runbook {} with version {} to marketplace".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing of marketplace runbook to marketplace failed")
        LOG.info("Success")

        # Try to delete the published runbook
        LOG.info("Negative Test: Deleting marketplace runbook in PUBLISHED state")
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
                "Deleting  of marketplace runbook should fail if runbook is in published state"
            )
        LOG.info("Success")

        # Unpublish marketplace runbook from marketplace
        LOG.info(
            "Unpublishing marketplace runboook {} with version {}".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "item",
            self.marketplace_rb_name,
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
            pytest.fail("Unpublishing of marketplace runboook failed")
        LOG.info("Success")

        # Deleting the Accepted marketplace runboook
        LOG.info(
            "Deleting marketplace runboook {} with version {} in ACCEPTED state".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Deletion of marketplace runboook in ACCEPTED state failed")
        LOG.info("Success")

        # Reject the marketplace runboook
        LOG.info(
            "Rejecting marketplace runboook {} with version {}".format(
                self.marketplace_rb_name, self.mpi2_version
            )
        )
        command = [
            "reject",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Rejection of marketplace runboook failed")
        LOG.info("Success")

        # Delete the rejected runboook
        LOG.info("Deleting marketplace runboook in REJECTED state")
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Deletion of marketplace runboook in REJECTED state failed")
        LOG.info("Success")

        # Delete the pending runboook
        LOG.info("Deleting marketplace runboook in PENDING state")
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Deletion of marketplace runboook in PENDING state failed")
        LOG.info("Success")

    def test_publish_to_marketplace_flag(self):
        """Test for publish_to_marketplace_flag for publsh command"""

        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish runbook directly to marketplace using --publish_to_marketplace flag
        LOG.info(
            "Publishing runbook {} as new marketplace runboook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing runbook using publish_to_marketplace flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )
        runbook_state = mpi_data["status"]["resources"]["app_state"]
        assert runbook_state == MARKETPLACE_ITEM.STATES.PUBLISHED

        LOG.info(
            "Unpublishing marketplace runboook {} with version {}".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "item",
            self.marketplace_rb_name,
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
            pytest.fail("Unpublishing of marketplace runboook failed")

        LOG.info(
            "Deleting marketplace runboook {} with version {} in ACCEPTED state".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Deletion of marketplace runboook in ACCEPTED state failed")

    def test_auto_approve_flag(self):
        """Test for auto_approve flag in publish command"""

        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        LOG.info(
            "Publishing runbook {} as new marketplace runboook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing runbook using auto_approve flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )
        runbook_state = mpi_data["status"]["resources"]["app_state"]
        assert runbook_state == MARKETPLACE_ITEM.STATES.ACCEPTED

        LOG.info(
            "Deleting marketplace runboook {} with version {} in ACCEPTED state".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Deletion of marketplace runboook in ACCEPTED state failed")

    def test_publish_runbook_with_icon(self):
        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)

        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi_version = "1.0.0"
        self.icon_name = "test_icon{}".format(str(uuid.uuid4())[:10])

        LOG.info("Publishing the runboook to marketplace manager")
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing of runboook as new marketplace item failed")
        LOG.info("Success")

        client = get_api_client()
        app_icon_name_uuid_map = client.app_icon.get_name_uuid_map()
        app_icon_uuid = app_icon_name_uuid_map.get(self.icon_name)

        runbook_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name, version=self.mpi_version
        )
        icon_reference = runbook_data["status"]["resources"]["icon_reference_list"][0][
            "icon_reference"
        ]
        assert (
            icon_reference["uuid"] == app_icon_uuid
        ), "App icon not used for the runbook"

        LOG.info(
            "Deleting the marketplace runboook {}".format(self.marketplace_rb_name)
        )
        result = runner.invoke(
            cli,
            [
                "delete",
                "marketplace",
                "runbook",
                self.marketplace_rb_name,
                "--version",
                self.mpi_version,
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
            pytest.fail("Deleting of marketplace runboook failed")

    def test_all_projects_flag_on_publising_runbook_with_auto_approve_flag(self):
        """Tests `--all_projects` flag to publish runbook to marketplace manager with auto approval flag"""

        client = get_api_client()
        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish runbook marketplace using --all_projects flag
        LOG.info(
            "Publishing runbook {} as new marketplace runboook {} with 'all_projects' flag".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing runbook using all_projects flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        runbook_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            runbook_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in runbook_projects

        self._delete_mpi()

    def test_all_projects_flag_on_approving_marketplace_bp(self):
        """Tests `--all_projects` flag to approving runbook to marketplace manager"""

        client = get_api_client()
        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish runbook to marketplace manager as new marketplace runboook
        LOG.info(
            "Publishing runbook {} as new marketplace runboook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
                "Publishing of marketplace runboook as new marketplace item failed"
            )

        # Approve the runboook
        LOG.info(
            "Approving marketplace runboook {} with version {} with 'all_projects' flag".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
                "Approving of marketplace runboook using all_projects flag failed"
            )
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        runbook_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            runbook_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in runbook_projects

        self._delete_mpi()

    def test_all_projects_flag_on_publishing_marketplace_bp(self):
        """Tests `--all_projects` flag for publishing runbook to marketplace store"""

        client = get_api_client()
        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish runbook directly to marketplace using --auto_approve flag
        LOG.info(
            "Publishing runbook {} as new marketplace runboook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing runbook using auto_approve flag failed")
        LOG.info("Success")

        # Publish runboook to marketplace
        LOG.info(
            "Publishing marketplace runboook {} with version {} to marketplace with 'all_projects' flag".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing of marketplace runboook to marketplace failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        runbook_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            runbook_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in runbook_projects

        # Unpublish marketplace runboook from marketplace
        LOG.info(
            "Unpublishing marketplace runboook {} with version {}".format(
                self.marketplace_rb_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "item",
            self.marketplace_rb_name,
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
            pytest.fail("Unpublishing of marketplace runboook to marketplace failed")
        LOG.info("Success")

    def test_all_projects_flag_on_publising_bp_without_auto_approve_flag(self):
        """Tests `--all_projects` flag to publish runbook to marketplace manager without auto approval flag"""

        client = get_api_client()
        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish runbook marketplace using --all_projects flag
        LOG.info(
            "Publishing runbook {} as new marketplace runboook {} with 'all_projects' flag".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
            pytest.fail("Publishing runbook using all_projects flag failed")
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        project_name_uuid_map = client.project.get_name_uuid_map({"length": 250})

        runbook_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            runbook_projects.append(_proj["name"])

        for _proj in project_name_uuid_map.keys():
            assert _proj in runbook_projects

        self._delete_mpi()

    def test_project_removal_flag_on_approving_marketplace_runbook(self):
        """Tests `--remove-project` flag on approving runbook to marketplace manager"""

        project_name = "default"  # This project will be removed while approving
        self._create_runbook(DSL_RB_FILEPATH)
        self.created_rb_list.append(self.created_dsl_rb_name)
        self.marketplace_rb_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish runbook to marketplace manager as new marketplace runbook with all projects
        LOG.info(
            "Publishing runbook {} as new marketplace runbook {}".format(
                self.created_dsl_rb_name, self.marketplace_rb_name
            )
        )
        command = [
            "publish",
            "runbook",
            self.created_dsl_rb_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_rb_name,
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
                "Publishing of marketplace runbook as new marketplace item failed"
            )

        # Approve the runbook
        LOG.info(
            "Approving marketplace runbook {} with version {} and removing {} project".format(
                self.marketplace_rb_name, self.mpi1_version, project_name
            )
        )
        command = [
            "approve",
            "marketplace",
            "runbook",
            self.marketplace_rb_name,
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
                "Approving of marketplace runbook using remove-project flag failed"
            )
        LOG.info("Success")

        mpi_data = get_mpi_by_name_n_version(
            name=self.marketplace_rb_name,
            version=self.mpi1_version,
            app_source=MARKETPLACE_ITEM.SOURCES.LOCAL,
        )

        runbook_projects = []
        for _proj in mpi_data["spec"]["resources"]["project_reference_list"]:
            runbook_projects.append(_proj["name"])

        assert project_name not in runbook_projects

        self._delete_mpi()

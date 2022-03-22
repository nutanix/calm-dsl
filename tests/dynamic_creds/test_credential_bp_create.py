import pytest
import uuid
import traceback
import json

from calm.dsl.log import get_logging_handle
from click.testing import CliRunner
from calm.dsl.cli import main as cli
from tests.utils import Application as ApplicationHelper

LOG = get_logging_handle(__name__)

SIMPLE_BLUEPRINT = "tests/dynamic_creds/test_credential_bp.py"
PROJECT_NAME = "test_dyn_cred_project"


class TestDynamicCredBps:
    app_helper = ApplicationHelper()

    @pytest.mark.parametrize(
        "bp_file_path",
        [SIMPLE_BLUEPRINT],
    )
    def test_dynamic_cred_bp_launch(self, bp_file_path):
        """
        This routine creates a blueprint with dynamic cred and launch app
        """
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        runner = CliRunner()

        LOG.info("Creating Bp {}".format(bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_file_path),
                "--name={}".format(bp_name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )

        LOG.debug("Response: {}".format(result.output))
        assert result.exit_code == 0

        # Create application
        app_name = "App{}".format(str(uuid.uuid4())[:10])
        LOG.info("Creating App {}".format(app_name))
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                bp_name,
                "--app_name={}".format(app_name),
                "--ignore_runtime_variables",
            ],
        )
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Creation of app {} failed".format(app_name))

        # Wait for app creation completion
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))

    @pytest.mark.parametrize(
        "bp_file_path",
        [SIMPLE_BLUEPRINT],
    )
    def test_dyn_cred_marketplace_launch(self, bp_file_path):
        """
        This routine publishes a blueprint with dynamic cred and launch app
        from marketplace
        """
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        runner = CliRunner()

        LOG.info("Creating Bp {}".format(bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_file_path),
                "--name={}".format(bp_name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )

        LOG.debug("Response: {}".format(result.output))
        assert result.exit_code == 0

        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"

        # Publish Bp to marketplace manager as new marketplace blueprint
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            bp_name,
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
            PROJECT_NAME,
            "--app_name",
            self.published_mpbp_app_name,
            "--profile_name",
            "DefaultProfile",
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

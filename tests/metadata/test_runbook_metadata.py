import uuid
import json
import traceback
import pytest
from click.testing import CliRunner


from calm.dsl.cli import main as cli
from calm.dsl.tools import make_file_dir
from calm.dsl.config import get_context
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_PROJECT_PATH = "tests/project/project_ntnx_local_account.py"
DSL_RUNBOOK_FILEPATH = "tests/metadata/runbook/runbook.py"
LOCAL_PROJECTNAME_FILE = "tests/metadata/runbook/.local/project_name"


class TestRunbookMetadata:
    def setup_method(self):
        """
        This method is used to create project
        """
        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

        runner = CliRunner()
        self.dsl_project_name = "test_dsl_project_{}".format(str(uuid.uuid4()))
        LOG.info("creating project {}".format(self.dsl_project_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "project",
                "--file={}".format(DSL_PROJECT_PATH),
                "--name={}".format(self.dsl_project_name),
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
            pytest.fail("Project creation from python file failed")

    def teardown_method(self):
        """
        This method is used to delete project
        """

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

        runner = CliRunner()
        LOG.info("deleting project {}".format(self.dsl_project_name))
        result = runner.invoke(cli, ["delete", "project", self.dsl_project_name])
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
            pytest.fail("Project deletion failed")

    def test_metadata_in_runbook(self):
        """
        This test is used to verify metadata in runbook file
        """
        runner = CliRunner()

        # Writing project name to project file for runbook
        make_file_dir(LOCAL_PROJECTNAME_FILE)
        with open(LOCAL_PROJECTNAME_FILE, "w") as f:
            f.write(self.dsl_project_name)

        # Compile runbook file
        LOG.info("Compiling runbook with metadata")
        result = runner.invoke(
            cli, ["compile", "runbook", "--file={}".format(DSL_RUNBOOK_FILEPATH)]
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
            pytest.fail("Runbook compile command failed")

        runbook_payload = json.loads(result.output)

        # Checking the presence of correct project in metadata
        LOG.info("Checking the project in metadata")
        assert (
            runbook_payload["metadata"]["project_reference"]["name"]
            == self.dsl_project_name
        )

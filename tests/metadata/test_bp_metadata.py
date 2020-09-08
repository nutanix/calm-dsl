import uuid
import json
import traceback
import pytest
from click.testing import CliRunner


from calm.dsl.cli import main as cli
from calm.dsl.tools import make_file_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_PROJECT_PATH = "tests/project/test_project_in_pc.py"
DSL_BP_FILEPATH = "tests/metadata/blueprint/blueprint.py"
LOCAL_PROJECTNAME_FILE = "tests/metadata/blueprint/.local/project_name"


class TestBlueprintMetadata:
    def setup_method(self):
        """Method to create project"""

        runner = CliRunner()
        self.dsl_project_name = "Test_DSL_Project_{}".format(str(uuid.uuid4()))
        result = runner.invoke(
            cli,
            [
                "create",
                "project",
                "--file={}".format(DSL_PROJECT_PATH),
                "--name={}".format(self.dsl_project_name),
                "--description='Test DSL Project to delete'",
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

        LOG.info("Updating cache to add project details")
        self._update_cache()

    def teardown_method(self):
        """Method to delete created project in setup method"""

        runner = CliRunner()
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

        LOG.info("Updating cache to remove project details")
        self._update_cache()

    def test_metadata_in_blueprint(self):
        """
        Tests metadata in blueprint file
        """

        runner = CliRunner()

        # Writing project name to project file for blueprint
        make_file_dir(LOCAL_PROJECTNAME_FILE)
        with open(LOCAL_PROJECTNAME_FILE, "w") as f:
            f.write(self.dsl_project_name)

        # Compile Blueprint file
        LOG.info("Compiling Blueprint with metadata")
        result = runner.invoke(
            cli, ["compile", "bp", "--file={}".format(DSL_BP_FILEPATH)]
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
            pytest.fail("BP compile command failed")

        bp_payload = json.loads(result.output)

        # Checking the presence of correct project in metadata
        LOG.info("Checking the project in metadata")
        assert (
            bp_payload["metadata"]["project_reference"]["name"] == self.dsl_project_name
        )

    def _update_cache(self):

        runner = CliRunner()
        result = runner.invoke(cli, ["update", "cache"])
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
            pytest.fail("Cache update command failed")

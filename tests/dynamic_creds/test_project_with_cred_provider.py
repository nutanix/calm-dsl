import pytest
import json
import uuid
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_PROJECT_PATH = "tests/dynamic_creds/demo_project.py"


class TestProjectCredProvider:
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

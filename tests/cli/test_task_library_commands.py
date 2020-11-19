import pytest
import time
import json
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


DSL_TL_FILEPATH = "tests/task_library/test_task_library_item.py"
SCRIPT_TL_FILEPATH = "tests/task_library/scripts/Install_IIS.ps1"
JSON_TL_FILEPATH = "tests/task_library/test_task_library_item.json"


@pytest.mark.slow
class TestTaskLibraryCommands:
    def test_task_library_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "library", "tasks"])
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
            pytest.fail("Task Library items Get failed")
        LOG.info("Success")

    def test_task_library_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["get", "library", "tasks", "--limit=15", "--offset=5"]
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
            pytest.fail("Task library list with limit call failed")
        LOG.info("Success")

    def test_task_library_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "library", "tasks", "--name='Install IIS'"])
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
            pytest.fail("Task library with name call failed")
        LOG.info("Success")

    def test_script_task_library_import(self):
        runner = CliRunner()
        self.created_script_tl_name = "Test_Task_Library_Script_{}".format(
            int(time.time())
        )
        LOG.info("Importing task library from script {}".format(SCRIPT_TL_FILEPATH))
        result = runner.invoke(
            cli,
            [
                "import",
                "library",
                "task",
                "--file={}".format(SCRIPT_TL_FILEPATH),
                "--name={}".format(self.created_script_tl_name),
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
            pytest.fail("Task library import command failed")
        LOG.info("Success")
        self._test_script_task_library_delete()

    def test_dsl_task_library_create(self):
        runner = CliRunner()
        self.created_dsl_tl_name = "Test_Task_Library_DSL_{}".format(int(time.time()))
        LOG.info("Creating Task library {}".format(self.created_dsl_tl_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "library",
                "task",
                "--file={}".format(DSL_TL_FILEPATH),
                "--name={}".format(self.created_dsl_tl_name),
                "--description='Test DSL Task library; to delete'",
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
            pytest.fail("Task library creation from python file failed")
        LOG.info("Success")
        self._test_task_library_describe()

    def test_json_task_library_create(self):
        runner = CliRunner()
        self.created_json_tl_name = "Test_Existing_TL_JSON_{}".format(int(time.time()))

        LOG.info("Creating Task Library {}".format(self.created_json_tl_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "library",
                "task",
                "--file={}".format(JSON_TL_FILEPATH),
                "--name={}".format(self.created_json_tl_name),
                "--description='Test JSON Task library; to delete'",
            ],
            catch_exceptions=True,
        )
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
            pytest.fail("Task Library creation from python file failed")
        LOG.info("Success")

        self._test_json_task_library_delete()

    def _test_task_library_describe(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["describe", "library", "task", self.created_dsl_tl_name]
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
        self._test_dsl_task_library_delete()

    def test_random_task_library_describe(self):
        runner = CliRunner()
        LOG.info("Running 'calm describe library task' command")
        tl_name = "MySQL_{}".format(int(time.time()))
        result = runner.invoke(cli, ["describe", "library", "task", tl_name])
        LOG.debug("Command output : {}".format(result.output))
        if result.exit_code != 0:
            assert result.exception.args[0] == "No task found with name {}".format(
                tl_name
            )
        else:
            assert result.exit_code == 0
        LOG.info("Success")

    def _test_dsl_task_library_delete(self):
        runner = CliRunner()
        LOG.info("Deleting DSL task library {} ".format(self.created_dsl_tl_name))
        result = runner.invoke(
            cli, ["delete", "library", "task", self.created_dsl_tl_name]
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
        LOG.info("Success")

    def _test_json_task_library_delete(self):
        runner = CliRunner()
        LOG.info("Deleting JSON Task Library {} ".format(self.created_json_tl_name))
        result = runner.invoke(
            cli, ["delete", "library", "task", self.created_json_tl_name]
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
        LOG.info("Success")

    def _test_script_task_library_delete(self):
        runner = CliRunner()
        LOG.info(
            "Deleting Imported Task library {} ".format(self.created_script_tl_name)
        )
        result = runner.invoke(
            cli, ["delete", "library", "task", self.created_script_tl_name]
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
        LOG.info("Success")


if __name__ == "__main__":
    tester = TestTaskLibraryCommands()

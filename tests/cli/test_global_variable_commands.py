import pytest
import uuid
import json
import traceback
import os
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.api import get_api_client

LOG = get_logging_handle(__name__)


GV_CREATE_JSON_FILEPATH = "tests/example_global_variables/json/test_gv_create.json"
GV_UPDATE_JSON_FILEPATH = "tests/example_global_variables/json/test_gv_update.json"

GV_CREATE_DSL_FILEPATH = "tests/example_global_variables/dsl/test_gv_create.py"
GV_UPDATE_DSL_FILEPATH = "tests/example_global_variables/dsl/test_gv_update.py"


@pytest.mark.global_variables
class TestGlobalVariableCommands:
    def setup_method(self):
        """Method to instantiate common variables for tests"""
        self.gv_uuid = ""

    @pytest.mark.parametrize(
        "create_gv_file_path, update_gv_file_path",
        [
            (GV_CREATE_JSON_FILEPATH, GV_UPDATE_JSON_FILEPATH),
            (GV_CREATE_DSL_FILEPATH, GV_UPDATE_DSL_FILEPATH),
        ],
    )
    def test_create_global_variable_command(
        self, create_gv_file_path, update_gv_file_path
    ):
        client = get_api_client()

        runner = CliRunner()
        self.created_gv_name = "Test_GlobalVar_DSL_{}".format(str(uuid.uuid4())[-10:])
        LOG.info("Creating Global variable {}".format(self.created_gv_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "global-variable",
                "--file={}".format(create_gv_file_path),
                "--name={}".format(self.created_gv_name),
            ],
        )

        params = {"filter": "name=={}".format(self.created_gv_name)}
        res, err = client.global_variable.list(params=params)
        response = res.json()

        if err:
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
            pytest.fail("Global variable creation from python file failed")

        self.gv_uuid = (
            response.get("entities", [{}])[0].get("metadata", {}).get("uuid", "")
        )

        gv_status = response.get("entities", [{}])[0].get("status", {}).get("state", "")

        assert (gv_status == "ACTIVE") or (gv_status == "DRAFT")

        LOG.info("Global variable Creation Successfull")

        self._test_update_global_variable(update_gv_file_path)

    def _test_update_global_variable(self, update_gv_file_path):

        runner = CliRunner()
        client = get_api_client()

        LOG.info("Updating Global variable {}".format(self.created_gv_name))
        result = runner.invoke(
            cli,
            [
                "update",
                "global-variable",
                self.created_gv_name,
                "--file={}".format(update_gv_file_path),
            ],
        )

        params = {"filter": "name=={}".format(self.created_gv_name)}
        res, err = client.global_variable.list(params=params)
        response = res.json()

        if err:
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
            pytest.fail("Global variable updation from python file failed")

        gv_status = response.get("entities", [{}])[0].get("status", {}).get("state", "")

        assert (gv_status == "ACTIVE") or (gv_status == "DRAFT")

        LOG.info("Global variable updation successful")

        self._test_global_variable_usage()

    def _test_global_variable_usage(self):
        """Test to check if global variable usage command works as expected"""

        # The name and UUID to be used in the test
        gv_name = self.created_gv_name
        gv_uuid = "123"

        # Mock response for list (to get UUID)
        list_mock_response = MagicMock()
        list_mock_response.json.return_value = {
            "entities": [{"metadata": {"uuid": gv_uuid}}]
        }

        # Mock response for usage (to get usage info)
        usage_mock_response = MagicMock()
        usage_mock_response.json.return_value = {
            "status": {
                "usage": {
                    "runbook": 2,
                },
                "resources": {
                    "runbook_list": [{"name": "test_rb_1"}, {"name": "test_rb_2"}],
                    "blueprint_list": [],
                    "marketplace_item_list": [],
                    "app_list": [],
                },
            }
        }

        with patch(
            "calm.dsl.cli.global_variable.get_api_client"
        ) as mock_get_api_client:
            mock_client = MagicMock()
            mock_client.global_variable.list.return_value = (list_mock_response, None)
            mock_client.global_variable.usage.return_value = (usage_mock_response, None)
            mock_get_api_client.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["get", "usage", "global-variable", gv_name],
            )

            assert result.exit_code == 0, "Global variable usage command failed"
            assert "test_rb_1, test_rb_2" in result.output

        self._test_global_variable_delete()

    def _test_global_variable_delete(self):
        """Test to check if global variable delete command works as expected"""
        runner = CliRunner()
        LOG.info("Deleting Global variable invalid_name")
        result = runner.invoke(
            cli,
            ["delete", "global-variable", "invalid_name"],
        )
        assert (
            result.exit_code != 0
        ), "Expected failure for invalid global variable name"
        assert result.output == "No global variable found with name invalid_name\n"

        LOG.info("Deleting Global variable {}".format(self.created_gv_name))
        result = runner.invoke(
            cli,
            ["delete", "global-variable", self.created_gv_name],
        )

        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Deleting global variable failed: {}".format(result.output))

        LOG.info("Global variable deletion successful")

    def test_global_variable_decompile(self):
        runner = CliRunner()
        GV_DIR = "tests/example_global_variables/json"
        gv_file_location = os.path.join(os.getcwd(), GV_DIR, "test_gv_create.json")

        LOG.info("decompiling global variable file at {}".format(gv_file_location))
        result = runner.invoke(
            cli, ["-vv", "decompile", "global-variable", "-f", gv_file_location]
        )
        assert (
            not result.exit_code
        ), "global variable decompile expected to pass but failed for {}".format(
            gv_file_location
        )

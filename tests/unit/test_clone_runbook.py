import pytest
import os
import time
import json
import uuid
import click
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.store.version import Version
from distutils.version import LooseVersion as LV

LOG = get_logging_handle(__name__)

CALM_VERSION = Version.get_version("Calm")

DSL_RB_FILEPATH = "tests/sample_runbooks/simple_runbook.py"


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("4.0.0"),
    reason="Tests for runbook clone changes are introduced in 4.0.0",
)
class TestRBCloneCommand:
    def setup_method(self):
        """Method to instantiate to created_rb_list"""

        self.created_rb_list = []

    def teardown_method(self):
        """Method to delete created runbooks during tests"""

        for rb_name in self.created_rb_list:
            LOG.info("Deleting Runbook {}".format(rb_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "runbook", rb_name])
            assert result.exit_code == 0

        self.created_rb_list = []

    def _create_rb(self, file, name):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "runbook",
                "--file={}".format(file),
                "--name={}".format(name),
                "--description='Test DSL Runbook; to delete'",
                "--force",
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.info(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("RB creation failed")

    def _test_rb_clone(self, original_rb_name, cloned_rb_name):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "clone",
                "runbook",
                original_rb_name,
                cloned_rb_name,
            ],
        )
        return result

    def test_rb_clone_command(self):
        """
        Test 'calm clone runbook' command
        """
        LOG.info("Testing 'calm clone runbook' command")
        self.original_rb_name = "original_runbook" + str(uuid.uuid4())[-10:]
        self._create_rb(DSL_RB_FILEPATH, self.original_rb_name)
        self.created_rb_list.append(self.original_rb_name)
        self.cloned_rb_name = "cloned_runbook" + str(uuid.uuid4())[-10:]
        self.created_rb_list.append(self.cloned_rb_name)

        result = self._test_rb_clone(self.original_rb_name, self.cloned_rb_name)

        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.info(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.info(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("RB clone call failed")
        LOG.info("Success")

    def test_rb_clone_command_with_duplicate_name(self):
        """
        Test 'calm clone runbook' command with runbook with duplicate name
        """
        LOG.info(
            "Testing 'calm clone runbook' command with runbook with duplicate name"
        )

        self.original_rb_name_duplicate = "original_runbook" + str(uuid.uuid4())[-10:]
        self._create_rb(DSL_RB_FILEPATH, self.original_rb_name_duplicate)
        self.created_rb_list.append(self.original_rb_name_duplicate)

        result = self._test_rb_clone(
            self.original_rb_name_duplicate, self.original_rb_name_duplicate
        )

        if not result.exit_code:
            pytest.fail("RB clone call  with runbook with duplicate name failed")
        LOG.info("Success")

    def test_rb_clone_command_with_invalid_runbook(self):
        """
        Test 'calm clone runbook' command with runbook that does not exist
        """
        LOG.info(
            "Testing 'calm clone runbook' command with runbook that does not exist"
        )
        self.cloned_rb_name = "cloned_runbook" + str(uuid.uuid4())[-10:]
        self.invalid_rb_name = "invalid_runbook" + str(uuid.uuid4())[-10:]

        result = self._test_rb_clone(self.invalid_rb_name, self.cloned_rb_name)

        if not result.exit_code:
            pytest.fail("RB clone call  with runbook with duplicate name failed")
        LOG.info("Success")

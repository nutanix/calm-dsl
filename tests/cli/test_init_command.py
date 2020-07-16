import os
import time
import json
import traceback
import pytest
import shutil
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def test_init_bp():

    bp_name = "Test_Bp_{}".format(int(time.time()))
    dir_name = os.getcwd()
    LOG.info("Creating bp directory at {}".format(dir_name))

    runner = CliRunner()
    result = runner.invoke(
        cli, ["init", "bp", "--name", bp_name, "--dir_name", dir_name]
    )

    if result.exit_code:
        cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
        LOG.debug(
            "Cli Response: {}".format(
                json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
            )
        )
        LOG.debug(
            "Traceback: \n{}".format("".join(traceback.format_tb(result.exc_info[2])))
        )
        pytest.fail("calm init bp command failed")

    # Deleting bp directory
    BP_DIR = os.path.join(dir_name, "{}Blueprint".format(bp_name))
    LOG.info("Deleting bp directory at {}".format(BP_DIR))
    shutil.rmtree(BP_DIR)
    LOG.info("Success")

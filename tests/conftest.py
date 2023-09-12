import sys
import pytest
import logging
import json
import os

from pytest_reportportal import RPLogger, RPLogHandler
from calm.dsl.log import CustomLogging, get_logging_handle
from calm.dsl.builtins import read_local_file
from tests.utils import ReportPortal

LOG = get_logging_handle(__name__)


@pytest.fixture(scope="session", autouse=True)
def rp_logger(request):
    """
    This routine is to create reportportal handler.
    Args:
        request(object): pytest test object
    Returns:
        logger (object) : logger object
    """

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if hasattr(request.node.config, "py_test_service"):
        logging.setLoggerClass(RPLogger)
        rp_handler = RPLogHandler(request.node.config.py_test_service)
        CustomLogging.IS_RP_ENABLED = True

        # Set verbose logs to DEBUG
        CustomLogging.set_verbose_level(lvl=CustomLogging.DEBUG)

        # Skipping logs via peewee db-orm
        logger = logging.getLogger("peewee")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.ERROR)
    else:
        rp_handler = logging.StreamHandler(sys.stdout)

    rp_handler.setLevel(logging.DEBUG)
    return logger


def pytest_collection_modifyitems(config, items):
    """
    This routine helps to add pytest marker to the tests based on the parameters of the tests
    Args:
        config(obj): pytest config object
        items(list): list of item objects
    """
    print("Inside conftests")
    if os.environ.get("CALM_DSL_TESTS") == "MOCK":
        return

    DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

    query_param = {
        "failed_tests": ("&filter.in.issue$issue_type=TI001", "failed_test"),
        "rerunteststype": ("&filter.in.issue$issue_type=TI001", "failed_test"),
        "notrun_tests": (None, "notrun_test"),
    }

    if DSL_CONFIG["reportportal"]["run_type"] == "re_run":
        run_name = DSL_CONFIG["reportportal"]["run_name"]
        run_number = int(DSL_CONFIG["reportportal"]["run_number"])
        token = DSL_CONFIG["reportportal"]["token"]

        rp_helper = ReportPortal(token)

        LOG.info(
            "Getting launch ID of run name: {}, number: {}".format(run_name, run_number)
        )
        launch_id = rp_helper.get_launch_id(run_name, run_number)

        to_run_tests = rp_helper.get_tests(
            launch_id, query_param[DSL_CONFIG["reportportal"]["rerun_tests_type"]][0]
        )
        deselected_items = []
        count = 0

    for item in items:
        if DSL_CONFIG["reportportal"]["run_type"] == "re_run":
            if (
                query_param[DSL_CONFIG["reportportal"]["rerun_tests_type"]][1]
                == "failed_test"
            ):
                if item.name not in to_run_tests:
                    count = count + 1
                    deselected_items.append(item)
            elif (
                query_param[DSL_CONFIG["reportportal"]["rerun_tests_type"]][1]
                == "notrun_test"
            ):
                if item.name in to_run_tests:
                    count = count + 1
                    deselected_items.append(item)
            else:
                LOG.error(
                    "Invalid rerun tests type: {}".format(
                        query_param[DSL_CONFIG["reportportal"]["rerun_tests_type"]][1]
                    )
                )

    if DSL_CONFIG["reportportal"]["run_type"] == "re_run":
        items[:] = [item for item in items if item not in deselected_items]
        config.hook.pytest_deselected(items=deselected_items)
        LOG.info("Total number of tests deselected for rerun is {}".format(str(count)))
        LOG.info("Total number of tests for rerun is {}".format(len(items)))

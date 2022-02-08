import json
import os
import sys
import pytest
import logging
from pytest_reportportal import RPLogger, RPLogHandler


from calm.dsl.api.handle import get_api_client
from calm.dsl.api.resource import get_resource_api
from calm.dsl.log import CustomLogging, get_logging_handle

LOG = get_logging_handle(__name__)
HOME = os.path.expanduser("~")
DSL_TEST_FILES_PREFIX = HOME + "/.calm/.local/.tests/runbook_tests/"


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


def pytest_sessionfinish(session, exitstatus):
    """
    This routine is called after whole test run finished,
    right before returning the exit status to the system.
    Args:
        session (pytest.Session) – The pytest session object.
        exitstatus (int) – The status which pytest will return to the system
    """
    LOG.debug("All tests finished. Deleting VMs created by test setup of dsl.")
    vm_uuid_files = [
        "ahv_linux_id",
        "ahv_linux_id_with_no_ip",
        "ahv_linux_id_with_powered_off",
        "vm_actions_ahv_on",
        "vm_actions_ahv_off",
    ]

    # Read uuid of vms from files and delete them
    try:
        api_client = get_api_client()
        vm_obj = get_resource_api("vms", api_client.connection)
        for file_name in vm_uuid_files:
            vm_uuid = None
            file_name = DSL_TEST_FILES_PREFIX + file_name
            if os.path.exists(file_name):
                with open(file_name, "r") as fp:
                    vm_uuid = fp.read()

                try:
                    LOG.debug("Deleting vm with uuid {} .".format(vm_uuid))
                    res, err = vm_obj.delete(vm_uuid)
                    LOG.debug(
                        "Response for delete vm:{}".format(json.dumps(res.json()))
                    )
                    if err:
                        raise Exception(err)
                except Exception as ex:
                    LOG.debug(
                        "Delete of vm with uuid {} failed with error: {}. Try deleting manually.".format(
                            vm_uuid, ex
                        )
                    )
    except Exception as ex:
        LOG.debug(
            "Delete of vms failed with error: {}. Try deleting manually.".format(ex)
        )

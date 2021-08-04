import sys
import pytest
import logging
from pytest_reportportal import RPLogger, RPLogHandler

from calm.dsl.log import CustomLogging, get_logging_handle

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

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
    if hasattr(request.node.config, 'py_test_service'):
        logging.setLoggerClass(RPLogger)
        rp_handler = RPLogHandler(request.node.config.py_test_service)
        CustomLogging.IS_RP_ENABLED = True

        # Skipping logs via peewee db-orm
        logger = logging.getLogger('peewee')
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.ERROR)
    else:
        rp_handler = logging.StreamHandler(sys.stdout)

    rp_handler.setLevel(logging.DEBUG)
    return logger


def fix_logging_level_for_loggers(lvl=10):
    """
    helper fixes logging level for all loggers
    Every object of CustomLogging will have this level
    """

    # Set to debug mode
    CustomLogging.set_verbose_level(lvl=lvl)


fix_logging_level_for_loggers()

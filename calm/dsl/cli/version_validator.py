from distutils.version import LooseVersion as LV

from calm.dsl.store import Version
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)
LATEST_VERIFIED_VERSION = "2.9.7"


def validate_version():

    # At initializing dsl, version might not found in cache
    calm_version = Version.get_version("CALM")
    if calm_version:
        if LV(calm_version) < LV(LATEST_VERIFIED_VERSION):
            LOG.warning(
                "Host CALM version({}) is less than verified({}).".format(
                    calm_version, LATEST_VERIFIED_VERSION
                )
            )

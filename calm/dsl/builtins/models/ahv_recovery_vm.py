import sys
import uuid

from .entity import Entity, EntityType
from .validator import PropertyValidator
from .helper import common as common_helper
from .ahv_vm import AhvVmResourcesType

from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.api.handle import get_api_client
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# AhvRecoveryVm


class AhvVMRecoveryResourcesType(AhvVmResourcesType):
    """Metaclass for ahv vm recovery resources"""

    __schema_name__ = "AhvVmRecoveryResources"
    __openapi_type__ = "recovery_vm_ahv_resources"


class AhvVMRecoveryResourcesValidator(
    PropertyValidator, openapi_type="recovery_vm_ahv_resources"
):
    __default__ = None
    __kind__ = AhvVMRecoveryResourcesType


def _ahv_vm_recovery_resources(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvVMRecoveryResourcesType(name, bases, kwargs)


AhvVmRecoveryResources = _ahv_vm_recovery_resources()


# AhvVmRecoverySpec


class AhvVMRecoverySpecType(EntityType):
    """Metaclass for ahv vm recovery resources"""

    __schema_name__ = "AhvVmRecoverySpec"
    __openapi_type__ = "recovery_vm_ahv_spec"


class AhvVMRecoverySpecValidator(
    PropertyValidator, openapi_type="recovery_vm_ahv_spec"
):
    __default__ = None
    __kind__ = AhvVMRecoverySpecType


def ahv_vm_recovery_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvVMRecoverySpecType(name, bases, kwargs)


AhvVMRecoverySpec = ahv_vm_recovery_spec()

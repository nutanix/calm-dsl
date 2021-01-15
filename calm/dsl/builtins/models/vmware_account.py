from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER, PROVIDER_RESOURCE
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class VmwareAccountSpecType(AccountSpecType):
    __schema_name__ = "VmwareAccountSpec"
    __openapi_type__ = "vmware_account_spec"

    __provider_type__ = PROVIDER.VMWARE
    __resource_type__ = PROVIDER_RESOURCE.VMWARE.VM

    def compile(cls):
        """returns the compiled payload for azure account spec"""

        cdict = super().compile()
        password = cdict.pop("password", "")
        cdict["password"] = {"attrs": {"is_secret_modified": True}, "value": password}

        return cdict


class VmwareAccountSpecValidator(PropertyValidator, openapi_type="vmware_account_spec"):
    __default__ = None
    __kind__ = VmwareAccountSpecType


def vmware_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return VmwareAccountSpecType(name, bases, kwargs)


VmwareAccountSpec = vmware_account_spec()

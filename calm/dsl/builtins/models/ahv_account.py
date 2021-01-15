from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER, PROVIDER_RESOURCE
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class AhvAccountSpecType(AccountSpecType):
    __schema_name__ = "AhvAccountSpec"
    __openapi_type__ = "ahv_account_spec"

    __provider_type__ = PROVIDER.NUTANIX
    __resource_type__ = PROVIDER_RESOURCE.NUTANIX.VM

    def compile(cls):
        """returns the compiled payload for ahv account spec"""

        cdict = super().compile()
        password = cdict.pop("password", None)
        cdict["password"] = {"attrs": {"is_secret_modified": True}, "value": password}

        return cdict


class AhvAccountSpecValidator(PropertyValidator, openapi_type="ahv_account_spec"):
    __default__ = None
    __kind__ = AhvAccountSpecType


def ahv_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvAccountSpecType(name, bases, kwargs)


AhvAccountSpec = ahv_account_spec()

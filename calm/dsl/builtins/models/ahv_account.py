from .entity import Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle

from .account import AccountDataType


LOG = get_logging_handle(__name__)


class AhvAccountDataType(AccountDataType):
    __schema_name__ = "AhvAccountData"
    __openapi_type__ = "ahv_account_data"

    __provider_type__ = "nutanix_pc"

    def compile(cls):
        """returns the compiled payload for ahv account data"""

        cdict = super().compile()
        password = cdict.pop("password", None)
        cdict["password"] = {"attrs": {"is_secret_modified": True}, "value": password}

        return cdict


class AhvAccountDataValidator(PropertyValidator, openapi_type="ahv_account_data"):
    __default__ = None
    __kind__ = AhvAccountDataType


def ahv_account_data(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvAccountDataType(name, bases, kwargs)


AhvAccountData = ahv_account_data()

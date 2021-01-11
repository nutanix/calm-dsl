from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class GcpAccountSpecType(AccountSpecType):
    __schema_name__ = "GcpAccountSpec"
    __openapi_type__ = "gcp_account_spec"

    __provider_type__ = PROVIDER.GCP

    def compile(cls):
        """returns the compiled payload for ahv account spec"""

        cdict = super().compile()

        private_key = cdict.pop("private_key", None)
        cdict["private_key"] = {
            "attrs": {"is_secret_modified": True},
            "value": private_key,
        }

        region_list = cdict.pop("regions", None)
        cdict["regions"] = [{"name": rn} for rn in region_list]

        if not cdict.get("gke_config", None):
            cdict.pop("gke_config", None)

        return cdict


class GcpAccountSpecValidator(PropertyValidator, openapi_type="gcp_account_spec"):
    __default__ = None
    __kind__ = GcpAccountSpecType


def gcp_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return GcpAccountSpecType(name, bases, kwargs)


GcpAccountSpec = gcp_account_spec()

from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# GCP Account


class GcpAccountType(EntityType):
    __schema_name__ = "GcpAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.GCP

    def compile(cls):
        cdict = super().compile()

        private_key = cdict.pop("private_key", None)
        cdict["private_key"] = {
            "attrs": {"is_secret_modified": True},
            "value": private_key,
        }

        region_list = cdict.pop("regions", None)
        cdict["regions"] = [{"name": rn} for rn in region_list]

        if not cdict.get("gke_config"):
            cdict.pop("gke_config")

        return cdict


class GcpAccountValidator(PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.GCP):
    __default__ = None
    __kind__ = GcpAccountType


def gcp_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return GcpAccountType(name, bases, kwargs)


GcpAccountData = gcp_account()

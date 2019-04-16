from .entity import EntityType, Entity
from .validator import PropertyValidator


# Substrate


class SubstrateType(EntityType):
    __schema_name__ = "Substrate"
    __openapi_type__ = "app_substrate"

    def compile(cls):

        cdict = super().compile()

        # TODO - fix this mess!
        # readiness probe requires address to be set even if there is one nic

        if cdict["type"] == "AHV_VM":
            readiness_probe = {
                "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@"
            }

        elif cdict["type"] == "EXISTING_VM":
            readiness_probe = {"address": "@@{ip_address}@@"}

        else:
            readiness_probe = {}

        cdict["readiness_probe"] = readiness_probe

        return cdict


class SubstrateValidator(PropertyValidator, openapi_type="app_substrate"):
    __default__ = None
    __kind__ = SubstrateType


def substrate(**kwargs):
    name = getattr(SubstrateType, "__schema_name__")
    bases = (Entity,)
    return SubstrateType(name, bases, kwargs)


Substrate = substrate()

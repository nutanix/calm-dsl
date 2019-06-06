from .entity import EntityType, Entity
from .validator import PropertyValidator


# Substrate


class SubstrateType(EntityType):
    __schema_name__ = "Substrate"
    __openapi_type__ = "app_substrate"

    ALLOWED_FRAGMENT_ACTIONS = {
        "__pre_create__": "pre_action_create",
        "__post_delete__": "post_action_delete",
    }

    def compile(cls):

        cdict = super().compile()

        if "readiness_probe" in cdict and cdict["readiness_probe"]:
            readiness_probe = cdict["readiness_probe"]
        else:
            if cdict["type"] == "AHV_VM":

                # If readiness probe is not given by user, set defaults
                readiness_probe = {
                    "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                    "disable_readiness_probe": False,
                    "delay_secs": "0",
                    "connection_type": "SSH",
                    "connection_port": 22,
                }
            elif cdict["type"] == "EXISTING_VM":
                readiness_probe = {
                    "address": "@@{ip_address}@@",
                    "disable_readiness_probe": False,
                    "delay_secs": "0",
                    "connection_type": "SSH",
                    "connection_port": 22,
                }
            else:
                readiness_probe = {}

        cdict["readiness_probe"] = readiness_probe

        return cdict

    def get_task_target(cls):
        return cls.get_ref()


class SubstrateValidator(PropertyValidator, openapi_type="app_substrate"):
    __default__ = None
    __kind__ = SubstrateType


def substrate(**kwargs):
    name = getattr(SubstrateType, "__schema_name__")
    bases = (Entity,)
    return SubstrateType(name, bases, kwargs)


Substrate = substrate()

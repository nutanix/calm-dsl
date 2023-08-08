import sys
from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# Azure Account


class AzureAccount(EntityType):
    __schema_name__ = "AzureAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.AZURE

    def compile(cls):
        cdict = super().compile()
        client_key = cdict.pop("client_key", None)
        cdict["client_key"] = {
            "attrs": {"is_secret_modified": True},
            "value": client_key,
        }

        # TODO remove from here
        if cdict["cloud_environment"] not in [
            "PublicCloud",
            "GermanCloud",
            "ChinaCloud",
            "USGovernmentCloud",
        ]:
            LOG.error(
                "Invalid cloud environment '{}' given.".format(
                    cdict["cloud_environment"]
                )
            )
            sys.exit("Invalid cloud environmend")

        if not cdict.get("subscriptions", []):
            cdict.pop("subscriptions", None)

        if not cdict.get("default_subscription", ""):
            cdict.pop("default_subscription", None)

        return cdict


class AzureAccountValidator(PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.AZURE):
    __default__ = None
    __kind__ = AzureAccount


def azure_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return AzureAccount(name, bases, kwargs)


AzureAccountData = azure_account()

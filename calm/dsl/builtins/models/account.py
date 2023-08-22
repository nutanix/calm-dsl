from .entity import Entity, EntityType, EntityDict
from .validator import PropertyValidator, get_property_validators
from .vmware_account import VmwareAccountType
from .custom_provider_account import CustomProviderType
from calm.dsl.constants import ACCOUNT, ENTITY
from types import MappingProxyType

from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)

# Account


class AccountResourcesDict(EntityDict):
    def pre_validate(cls, vdict, name, value, parent=None):

        namespace_dict = parent.__dict__.get("__namespace_dict__", "")
        account_type = namespace_dict.get("type", "")

        property_validators = get_property_validators()

        account_type_map = {
            ACCOUNT.TYPE.AHV: property_validators[ENTITY.OPENAPI_TYPE.AHV],
            ACCOUNT.TYPE.AZURE: property_validators[ENTITY.OPENAPI_TYPE.AZURE],
            ACCOUNT.TYPE.AWS: property_validators[ENTITY.OPENAPI_TYPE.AWS],
            ACCOUNT.TYPE.AWS_C2S: property_validators[ENTITY.OPENAPI_TYPE.AWS_C2S],
            ACCOUNT.TYPE.K8S_VANILLA: property_validators[
                ENTITY.OPENAPI_TYPE.K8S_VANILLA
            ],
            ACCOUNT.TYPE.K8S_KARBON: property_validators[
                ENTITY.OPENAPI_TYPE.K8S_KARBON
            ],
            ACCOUNT.TYPE.VMWARE: property_validators[ENTITY.OPENAPI_TYPE.VMWARE],
            ACCOUNT.TYPE.GCP: property_validators[ENTITY.OPENAPI_TYPE.GCP],
            ACCOUNT.TYPE.CREDENTIAL_PROVIDER: property_validators[
                ENTITY.OPENAPI_TYPE.CREDENTIAL_PROVIDER
            ],
            ACCOUNT.TYPE.NDB: property_validators[ENTITY.OPENAPI_TYPE.CUSTOM_PROVIDER],
        }

        if "resources" in vdict:
            new_dict = dict(vdict)
            if account_type:
                new_dict["resources"] = (account_type_map[account_type], False)
            vdict = MappingProxyType(new_dict)

        return vdict, value


class AccountType(EntityType):
    """Metaclass for account"""

    __schema_name__ = "Account"
    __openapi_type__ = "app_account"
    __prepare_dict__ = AccountResourcesDict

    def compile(cls):
        cdict = super().compile()

        if cdict["type"] in ["k8s_vanilla", "k8s_karbon"]:
            cdict["type"] = "k8s"

        if cdict["type"] == "vmware":
            if "price_items" in dir(cdict["data"]):
                price_items = VmwareAccountType.compile(cdict["data"]).pop(
                    "price_items", {}
                )
                cdict["price_items"] = price_items
                delattr(cdict["data"], "price_items")

        if cdict["type"] == "NDB":
            if "parent_reference" in dir(cdict["data"]):
                parent_reference = CustomProviderType.compile(cdict["data"]).pop(
                    "parent_reference", {}
                )
                cdict["parent_reference"] = parent_reference
                delattr(cdict["data"], "parent_reference")

        return cdict


class AccountValidator(PropertyValidator, openapi_type="app_account"):
    __default__ = None
    __kind__ = AccountType


def _account_payload(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return AccountType(name, bases, kwargs)


Account = _account_payload()

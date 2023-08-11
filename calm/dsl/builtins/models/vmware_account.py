import uuid

from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY

LOG = get_logging_handle(__name__)

# AHV Account


class VmwareAccountType(EntityType):
    __schema_name__ = "VmwareAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.VMWARE

    def create_price_item_list(cls, price_items):
        cost_list = []

        for price_item in price_items:
            name = price_item
            if price_item == "vcpu":
                name = "sockets"

            cost_list.append(
                {"interval": "hour", "name": name, "value": price_items[price_item]}
            )

        state_cost_list = [
            {"state": "ON", "cost_list": cost_list},
            {
                "state": "OFF",
                "cost_list": [
                    {
                        "interval": "hour",
                        "name": "storage",
                        "value": price_items["storage"],
                    }
                ],
            },
        ]

        price_item_list = [
            {
                "details": {"occurrence": "recurring"},
                "state_cost_list": state_cost_list,
                "uuid": str(uuid.uuid4()),
            }
        ]

        return price_item_list

    def compile(cls):
        cdict = super().compile()

        password = cdict.pop("password", "")
        cdict["password"] = {"attrs": {"is_secret_modified": True}, "value": password}

        price_items = cdict.pop("price_items", {})
        if price_items:
            price_item_list = cls.create_price_item_list(price_items)
            cdict["price_items"] = price_item_list

        if not cdict.get("datacenter"):
            cdict.pop("datacenter", None)

        return cdict


class VmwareAccountValidator(
    PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.VMWARE
):
    __default__ = None
    __kind__ = VmwareAccountType


def vmware_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return VmwareAccountType(name, bases, kwargs)


VmwareAccountData = vmware_account()

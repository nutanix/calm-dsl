import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.constants import POLICY

LOG = get_logging_handle(__name__)

POLICY_EVENT_MAP = {
    POLICY.EVENT.APP.LAUNCH: "APP_LAUNCH",
    POLICY.EVENT.APP.DAY_TWO_OPERATION: "APP_DAY_TWO_OPERATION",
    POLICY.EVENT.RUNBOOK.EXECUTE: "RUNBOOK_EXECUTE",
}

PROVIDER_SUBSTRATE_TYPE_MAP = {
    "AHV": "AHV_VM",
    "VMWare": "VMWARE_VM",
    "Azure": "AZURE_VM",
    "AWS": "AWS_VM",
    "GCP": "GCP_VM",
}


def get_provider(attribute_name):
    provider_attribute_pair = attribute_name.split(":")
    if len(provider_attribute_pair) == 2:
        return provider_attribute_pair[0]
    return None


def get_criteria_list(attribute_dict, jsonpath):
    criteria_list = [
        {
            "operator": attribute_dict["operator"],
            "is_primary": True,
            "rhs": attribute_dict["value"],
            "lhs": jsonpath,
        }
    ]
    provider = get_provider(attribute_dict["attribute_name"])
    if provider:
        substrate_attribute_info = Cache.get_entity_data(
            entity_type=CACHE.ENTITY.POLICY_ATTRIBUTES,
            name="Substrate Type",
            event_name=POLICY_EVENT_MAP[POLICY.EVENT.APP.LAUNCH],
        )
        if not substrate_attribute_info:
            LOG.error(
                "No entry found for policy attribute: {}. Please check the name from Policy attributes table or "
                "update cache".format("Substrate Type")
            )
            sys.exit("No entry found for policy attribute={}".format("Substrate Type"))
        criteria_val = PROVIDER_SUBSTRATE_TYPE_MAP.get(provider, provider)
        criteria_list.append(
            {
                "operator": "=",
                "is_primary": False,
                "rhs": criteria_val,
                "lhs": substrate_attribute_info["jsonpath"],
            }
        )
    return criteria_list


class PolicyConditionType(EntityType):
    __schema_name__ = "PolicyCondition"
    __openapi_type__ = "policy_condition"

    def compile(cls):
        cdict = super().compile()
        policyObj = cls.__parent__
        attribute_info = Cache.get_entity_data(
            entity_type=CACHE.ENTITY.POLICY_ATTRIBUTES,
            name=cdict["attribute_name"],
            event_name=POLICY_EVENT_MAP[policyObj.event],
        )
        if not attribute_info:
            LOG.error(
                "No entry found for policy attribute: {}. Please check the name from Policy attributes table or "
                "update cache".format(cdict["attribute_name"])
            )
            sys.exit(
                "No entry found for policy attribute={}".format(cdict["attribute_name"])
            )
        criteria_list = get_criteria_list(cdict, attribute_info["jsonpath"])
        cdict.pop("operator", None)
        cdict.pop("value", None)
        cdict["criteria_list"] = criteria_list
        return cdict


class PolicyConditionValidator(PropertyValidator, openapi_type="policy_condition"):
    __default__ = None
    __kind__ = PolicyConditionType


def _policy_condition_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PolicyConditionType(name, bases, kwargs)


PolicyCondition = _policy_condition_payload()

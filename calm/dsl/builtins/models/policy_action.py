import sys

from .entity import EntityType, Entity
from calm.dsl.builtins import Ref
from .validator import PropertyValidator
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.approver_set import PolicyApproverSet

LOG = get_logging_handle(__name__)


class ATTRIBUTE_TYPE:
    APPROVER_SET = "approver_set_list"


class PolicyActionType(EntityType):
    __schema_name__ = "PolicyAction"
    __openapi_type__ = "policy_action"

    def get_attributes(cls, attribute_list):
        final_attrs = {}
        if attribute_list:
            if isinstance(attribute_list[0], type(PolicyApproverSet)):
                final_attrs[ATTRIBUTE_TYPE.APPROVER_SET] = attribute_list
            else:
                LOG.error("Not supported attribute type")
                sys.exit("Not supported attribute type")
        return final_attrs


class PolicyActionValidator(PropertyValidator, openapi_type="policy_action"):
    __default__ = None
    __kind__ = PolicyActionType


def _policy_action_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PolicyActionType(name, bases, kwargs)


PolicyAction = _policy_action_payload()

from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.constants import POLICY


class ApproverSetType(EntityType):
    __schema_name__ = "ApproverSet"
    __openapi_type__ = "approver_set"


class ApproverSetValidator(PropertyValidator, openapi_type="approver_set"):
    __default__ = None
    __kind__ = ApproverSetType


def _approver_set_payload(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ApproverSetType(name, bases, kwargs)


PolicyApproverSet = _approver_set_payload()


def create_policy_approver_set(
    name, type=POLICY.APPROVER_SET.ANY, users=None, groups=None, external_users=None
):
    return _approver_set_payload(
        name=name,
        type=type,
        users=[] if users is None else users,
        groups=[] if groups is None else groups,
        external_users=[] if external_users is None else external_users,
    )

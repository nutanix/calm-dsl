from .entity import EntityType, Entity
from calm.dsl.builtins import PolicyAction, _policy_action_payload
from calm.dsl.builtins.models.policy_condition import _policy_condition_payload
from calm.dsl.builtins import Ref
from .validator import PropertyValidator
from calm.dsl.constants import POLICY
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)

# Policy
class PolicyType(EntityType):
    __schema_name__ = "Policy"
    __openapi_type__ = "policy"

    def compile(cls):
        cdict = super().compile()
        cdict["event_reference"] = Ref.PolicyEvent(cdict["event_reference"])
        actions = cdict.get("action_list", []) or []
        if len(actions) > 1:
            LOG.warning("Only single action is supported in policies.")

        return cdict


class PolicyValidator(PropertyValidator, openapi_type="policy"):
    __default__ = None
    __kind__ = PolicyType


def policy(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PolicyType(name, bases, kwargs)


Policy = policy()


class CalmPolicy:
    """Helper class for policy"""

    class Approver:
        """Helper class for approver set in approval policy"""

        def __new__(cls, name):
            """Default case is for user type"""
            return Ref.User(name=name)

        class user:
            def __new__(cls, name):
                return Ref.User(name=name)

        class group:
            def __new__(cls, name):
                return Ref.Group(name=name)

        """
        # Not supported as of now
        class externalUser:
            def __new__(cls, email):
                return {"email": email}
        """

    class Action:
        """helper class to create policy actions"""

        class approvalAction:
            """helper class to create approval policy action"""

            def __new__(cls, approver_sets=None):
                return _policy_action_payload(
                    action_type=Ref.PolicyActionType(POLICY.ACTION_TYPE.APPROVAL),
                    attrs=PolicyAction.get_attributes(
                        approver_sets if approver_sets else []
                    ),
                )

    class Condition:
        """helper class to create policy conditions"""

        def __new__(cls, attribute, operator, value):
            return _policy_condition_payload(
                attribute=attribute, operator=operator, value=value
            )

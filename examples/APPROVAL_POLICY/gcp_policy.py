import json
from calm.dsl.builtins import CalmPolicy, Ref
from calm.dsl.builtins import Metadata, Policy, PolicyApproverSet
from calm.dsl.constants import POLICY
from calm.dsl.builtins import read_local_file
from tests.utils import get_approval_project


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
POLICY_PROJECT = get_approval_project(DSL_CONFIG)


# Select this option if you want any approvers selected for the set to approve the action.
class ApproverSet1(PolicyApproverSet):
    type = POLICY.APPROVER_SET.ANY
    users = [CalmPolicy.Approver.user("admin")]


# Select this option if you want all approvers in the set to approve the action.
class ApproverSet2(PolicyApproverSet):
    type = POLICY.APPROVER_SET.ALL
    users = [CalmPolicy.Approver.user("admin")]


class PolicyAprroval(Policy):
    """This policy gives sample on how any policy can be defined for GCP provider in calm-dsl."""

    # This defines the entity type and action on which the policy must be enforced on
    event = POLICY.EVENT.APP.LAUNCH

    # condition list
    conditions = [
        CalmPolicy.Condition(
            attribute="GCP: Zone", operator="contains", value="europe"
        ),
        CalmPolicy.Condition(attribute="GCP: Labels", operator="=", value="calm"),
    ]

    # if not defined Policy will be saved in Draft state
    actions = [CalmPolicy.Action.approvalAction(approver_sets=[ApproverSet2])]

    # default is false
    enabled = False


class PolicyMetadata(Metadata):
    project = Ref.Project(POLICY_PROJECT)

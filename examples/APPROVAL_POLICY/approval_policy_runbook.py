import json
from calm.dsl.builtins import CalmPolicy, Ref
from calm.dsl.builtins import Metadata, Policy, PolicyApproverSet
from calm.dsl.constants import POLICY
from calm.dsl.builtins import read_local_file
from tests.utils import get_approval_project


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
POLICY_PROJECT = get_approval_project(DSL_CONFIG)


class ApproverSet1(PolicyApproverSet):
    type = POLICY.APPROVER_SET.ANY
    users = [CalmPolicy.Approver.user("admin")]


class ApproverSet2(PolicyApproverSet):
    type = POLICY.APPROVER_SET.ALL
    users = [CalmPolicy.Approver.user("admin")]


class PolicyAprroval(Policy):
    """This policy gives sample on how any policy can be defined for runbook launch with conditions on endpoint name in calm-dsl."""

    # This defines the entity type and action on which the policy must be enforced on
    event = POLICY.EVENT.RUNBOOK.EXECUTE

    # condition list
    conditions = [
        CalmPolicy.Condition(
            attribute="Endpoint Name", operator="contains", value="calm"
        )
    ]

    # if not defined then it will be empty list
    actions = CalmPolicy.Action.approvalAction(approver_sets=[ApproverSet2])

    # default is false
    enabled = False


class PolicyMetadata(Metadata):
    project = Ref.Project(POLICY_PROJECT)

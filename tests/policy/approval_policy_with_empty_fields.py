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


class PolicyAprroval(Policy):
    """This policy is for a negative test which fails due to no event name given"""

    # condition list
    conditions = []

    # if not defined then it will be empty list
    actions = CalmPolicy.Action.approvalAction()

    # default is false
    enabled = False


class PolicyMetadata(Metadata):
    project = Ref.Project(POLICY_PROJECT)

import json

from calm.dsl.builtins import Policy, PolicyApproverSet, CalmPolicy, Ref, Metadata
from calm.dsl.builtins import read_local_file
from calm.dsl.constants import POLICY

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


class ApproverSet1(PolicyApproverSet):
    type = POLICY.APPROVER_SET.ANY
    external_users = [CalmPolicy.Approver.externalUser("abc@gmail.com")]
    # users = [CalmPolicy.Approver.user("ssptest1@qa.nucalm.io")]


class ApproverSet2(PolicyApproverSet):
    type = POLICY.APPROVER_SET.ALL
    external_users = [CalmPolicy.Approver.externalUser("abc@gmail.com")]
    # default case - if nothing specified after Approver it will assume it to be user
    # users = [CalmPolicy.Approver("ssptest1@qa.nucalm.io")]
    # groups = [
    #     CalmPolicy.Approver.group("cn=ssptestgroup,cn=users,dc=qa,dc=nucalm,dc=io")
    # ]


class UserTest(Policy):
    """This policy gives sample on how any policy can be defined in calm-dsl."""

    # This is required property to save policy
    event = POLICY.EVENT.APP.LAUNCH

    # condition list
    conditions = [
        CalmPolicy.Condition(attribute="AHV: vCPU", operator="=", value="45"),
        CalmPolicy.Condition(
            attribute="Blueprint Name", operator="like", value="Demo bp"
        ),
    ]

    # if not defined then it will be empty list
    actions = CalmPolicy.Action.approvalAction(
        approver_sets=[ApproverSet1, ApproverSet2]
    )

    # default is false
    enabled = True


class PolicyMetadata(Metadata):
    project = Ref.Project(PROJECT_NAME)

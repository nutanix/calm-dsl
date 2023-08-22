import json

from calm.dsl.builtins import (
    Policy,
    create_policy_approver_set,
    CalmPolicy,
    Ref,
    Metadata,
)
from calm.dsl.builtins import read_local_file
from calm.dsl.constants import POLICY


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


class UserTestMin(Policy):
    """This policy gives sample on how any policy can be defined in calm-dsl."""

    event = POLICY.EVENT.RUNBOOK.EXECUTE  # This is required property to save policy
    conditions = [
        CalmPolicy.Condition(
            attribute="Runbook Name", operator="like", value="Demo runbook"
        )
    ]
    actions = [
        CalmPolicy.Action.approvalAction(
            approver_sets=[
                create_policy_approver_set(
                    name="ApproverSet1",  # default is ""
                    type=POLICY.APPROVER_SET.ANY,  # default is "ANY"
                    users=[CalmPolicy.Approver("ssptest1@qa.nucalm.io")],  # default []
                    # external_users=[CalmPolicy.Approver.externalUser("abc@gmail.com")],  # default []
                ),
                create_policy_approver_set(
                    name="ApproverSet2",
                    type=POLICY.APPROVER_SET.ALL,  # default is "ANY"
                    users=[
                        CalmPolicy.Approver.user("ssptest1@qa.nucalm.io")
                    ],  # default []
                    groups=[
                        CalmPolicy.Approver.group(
                            "cn=ssptestgroup,cn=users,dc=qa,dc=nucalm,dc=io"
                        )
                    ],  # default []
                ),
            ]
        )
    ]  # if not defined then it will be empty list
    # enabled = true # default is false


class PolicyMetadata(Metadata):
    project = Ref.Project(PROJECT_NAME)

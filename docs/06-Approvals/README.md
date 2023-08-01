# Approvals

## CLI commands
### Policy
- Create Policy – `calm create policy -f <path to policy py file in policy> -n <policy name>`
- List Policies – `calm get policies`
- Get Policy Details - `calm describe policy <policy name>`
- Update Policy - `calm update policy -f <path to policy py filer in policy> -n <policy name>`
- Enable Policy - `calm enable policy <policy name>`
- Disable Policy - `calm disable policy <policy name>`
- Delete Policy – `calm delete policy <policy name>`
- Get Policy Executions - `calm get policy-executions <policy name>`
- Get Policy Execution Details - `calm describe policy-execution <policy name>`

### Approval Request
- List Approval requests – `calm get approval-requests`
- Get Approval request Details - `calm describe approval-request <approval name>`
- Approve Approval request - `calm approve approval-request <approval name>`
- Reject Approval request - `calm reject approvalrequest <approval name>`

### My Approval Request
- List My approval requests – `calm get my-approval-requests`
- Get My approval request Details - `calm describe my-approval-request <approval request name>`

## Built-in Models

- Added `Policy` model to create dsl-entity for defining policy.

- Added `PolicyApproverSet` model to create dsl-entity for defining policy approver set.

- Added `CalmPolicy.Approver.user` helper for defining approver user.

- Added `CalmPolicy.Approver.group` helper for defining approver group.

- Added `CalmPolicy.Condition` helper for defining policy condition.

- Added `CalmPolicy.Action.approvalAction` helper for defining approval action.

## Approver Set Types

List of supported approver set types-

- Any Approver - `POLICY.APPROVER_SET.ANY`
- All Approver - `POLICY.APPROVER_SET.ALL`

## Events

List of supported Events-

- App Launch - `POLICY.EVENT.APP.LAUNCH`
- App Day Two Operations - `POLICY.EVENT.APP.DAY_TWO_OPERATION`
- Runbook Execute - `POLICY.RUNBOOK.EXECUTE`

## Conditions

List of supported conditions can be found in cache data using command `calm show cache` inside
`POLICY_ATTRIBUTES` table, listing few here-

+-----------------------+-----------------------------------------------+--------+-----------------------------+
|       EVENT_NAME      |                      Name                     |  TYPE  |        OPERATOR_LIST        |
+-----------------------+-----------------------------------------------+--------+-----------------------------+
|       APP_LAUNCH      |                 Blueprint Name                | string |  ['=', 'contains', 'like']  |
|       APP_LAUNCH      |                  AHV: Memory                  | number | ['=', '<', '>', '>=', '<='] |
|         ...           |                     ...                       |   ...  |            ...              |
|    RUNBOOK_EXECUTE    |                  Runbook Name                 | string |  ['=', 'contains', 'like']  |
|         ...           |                     ...                       |   ...  |            ...              |
| APP_DAY_TWO_OPERATION |                  Action name                  | string |  ['=', 'contains', 'like']  |
+-----------------------+-----------------------------------------------+--------+-----------------------------+


## Sample examples:

### Approval policy for Application launch event.

- The Policy `Policy1` will take approval from `user1` on app laucnh with condition `AHV memory` greater than 5.

    ```
    from calm.dsl.builtins import CalmPolicy, Ref
    from calm.dsl.builtins import Metadata, Policy, PolicyApproverSet
    from calm.dsl.constants import POLICY

    class Set1(PolicyApproverSet):
        type = POLICY.APPROVER_SET.ANY
        users = [CalmPolicy.Approver.user("user1")]

    class Policy1(Policy):
        event = POLICY.EVENT.APP.LAUNCH
        conditions = [
            CalmPolicy.Condition(attribute="AHV: Memory", operator=">", value="5")
        ]
        actions = CalmPolicy.Action.approvalAction(
            approver_sets=[Set1]
        )
        enabled = True

    class PolicyMetadata(Metadata):
        project = Ref.Project("project1")
    ```

More examples can also be found in examples folder.

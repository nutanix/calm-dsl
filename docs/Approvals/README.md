# Table of Contents
- [CLI commands](#cli-commands)
  * [Policy](#policy)
  * [Approval Request](#approval-request)
  * [My Approval Request](#my-approval-request)
- [Built-in Models](#built-in-models)
  * [Approver-Set](#approver-set)
  * [Policy](#policy-1)
  * [Metadata](#metadata)


## CLI commands
### Policy
- Create Policy – `calm create policy -f <path to policy py file in policy> -n <policy name>`
- List Policies – `calm get policies`
- Get Policy Details - `calm describe policy <policy name>`
- Update Policy - `calm update policy <policy_name> -f <path to policy py filer in policy>`
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
Classes used in DSL code for Policies: 

### Approver-Set
For creation of approver-set, user need to define approver and approver-set type

- Defining approver: Approver can be of two types as follows:
    - Added `CalmPolicy.Approver.user` helper for defining approver user. E.g.: `CalmPolicy.Approver.user("admin")`
    - Added `CalmPolicy.Approver.group` helper for defining approver group. Ex: `CalmPolicy.Approver.group("group-name")`.
- Defining Approval-Set type. Approval-Set can be of two types as follows: 
    - Any Approver - `POLICY.APPROVER_SET.ANY`
    - All Approver - `POLICY.APPROVER_SET.ALL`
- Defining ApproverSet: Added `PolicyApproverSet` model to create dsl-entity for defining policy approver set.
    E.g.:
    ```
    class ApproverSet(PolicyApproverSet):
        type = POLICY.APPROVER_SET.ALL
        users = [CalmPolicy.Approver.user("admin")]
        groups = [CalmPolicy.Approver.group("group-1")]
    ```
### Policy
- Policy: Added `Policy` model to create dsl-entity for defining policy.
- User need to define event, conditions, action and policy-enablement status on the object:
    - Policy Condition
        - Defining Policy Condition: Added `CalmPolicy.Condition` helper for defining policy condition.
        - Example:
        ```
        CalmPolicy.Condition(attribute="AHV: Cores Per vCPU", operator=">", value="3")
        ```
        - List of supported attributes and operators can be found in cache data table 'POLCY_ATTRIBUTES' using command `calm show cache --type=policy_attributes`.
    
            | Event Name | Name | Type | Operation List |
            |------------|------|------|----------------|
            |  APP_LAUNCH | Blueprint Name | string | ['=', 'contains', 'like'] |
            |       APP_LAUNCH      |                  AHV: Memory                  | number | ['=', '<', '>', '>=', '<='] |
            |         ...           |                     ...                       |   ...  |            ...              |
            |    RUNBOOK_EXECUTE    |                  Runbook Name                 | string |  ['=', 'contains', 'like']  |
            |         ...           |                     ...                       |   ...  |            ...              |
            | APP_DAY_TWO_OPERATION |                  Action name                  | string |  ['=', 'contains', 'like']  |

    - Policy Action: Action are the entities which are executed whenever the policy is triggered.
        - Defining approval action: Added `CalmPolicy.Action.approvalAction` helper for defining approval action.
        - Example:
            ```
            CalmPolicy.Action.approvalAction(approver_sets=[ApproverSet2])
            ```
    - Policy Event Type: Event can be operated on application actions and runbooks as follows:
      - Application Action:
        - Launch: `POLICY.EVENT.APP.LAUNCH`
        - Day-2 action: `POLICY.EVENT.APP.DAY_TWO_OPERATION`
      - Runbook:
        - Execute: `POLICY.EVENT.RUNBOOK.EXECUTE`
    - Policy State: Used to define the state of policy. Allowed values are `true/false`.
        - Default state is `disabled`.
        - Example:
            ```
            class PolicyAprroval(Policy):

                enabled = True
            ```
- Example:
    ```
    class PolicyAprroval(Policy):
        """This policy gives sample on how any policy can be defined with AHV provider calm-dsl."""
    
        # This defines the entity type and action on which the policy must be enforced on
        event = POLICY.EVENT.APP.LAUNCH
    
        # condition list
        conditions = [
            CalmPolicy.Condition(attribute="AHV: Cores Per vCPU", operator=">", value="3"),
            CalmPolicy.Condition(attribute="AHV: Memory", operator="<", value="5")
        ]
    
    
        # if not defined Policy will be saved in Draft state
        actions = [CalmPolicy.Action.approvalAction(
            approver_sets=[ApproverSet2]
        )]
    
        # default is false
        enabled = True
    ```
    
### Metadata
User can use existing metadata model to define metadata i.e project-configuration etc.
Example:
```
class PolicyMetadata(Metadata):
    project = Ref.Project("POLICY_PROJECT_NAME")

```

More examples can also be found in [examples folder](../../examples/APPROVAL_POLICY).

from calm.dsl.builtins import Ref, CalmVariable
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable, runbook

# Provider with name "HelloProvider" & ResourceType with name "HelloResourceType" should already exist
PROVIDER_NAME = "HelloProvider"
RESOURCE_TYPE_NAME = "HelloResourceType"


@runbook
def Hello():
    runbook_var = RunbookVariable.Simple.string(
        value="user_val", is_mandatory=True, runtime=True
    )
    Task.ResourceTypeAction(
        "CustomProviderTask",
        Ref.Resource_Type(name=RESOURCE_TYPE_NAME, provider_name=PROVIDER_NAME),
        account_ref=Ref.Account(name="HelloAccount"),
        action_ref=Ref.ResourceTypeAction(
            name="Create",
            resource_type_name=RESOURCE_TYPE_NAME,
            provider_name=PROVIDER_NAME,
        ),
        inarg_list=[
            CalmVariable.Simple.string(
                name="input_var", value="@@{runbook_var}@@", is_mandatory=True
            )
        ],
        output_variables={"myoutput": "output_var"},
    )
    Task.Exec.escript(name="Verify mapped outputs", script="print('@@{myoutput}@@')")

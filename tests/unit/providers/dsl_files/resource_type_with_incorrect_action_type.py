from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins import (
    CalmVariable,
    CloudProvider,
    action,
    ProviderEndpointSchema,
    ResourceType,
    action,
)


class DSLResourceTypeWithIncorrectActionType(ResourceType):
    """Sample ResourceType"""

    resource_kind = "CUSTOM"

    @action
    def List(type="sseedeeded"):
        """List Action for HelloResourceType"""
        outputs = [CalmVariable.Simple.string(name="resource_ids", value="")]
        Task.SetVariable.escript(
            name="List Resources",
            variables=["resource_ids"],
            script="print (\"resource_ids = ['resource1', 'resource2']\")",
        )


class DslProvider(CloudProvider):

    """Sample provider with authentication schema, variables & custom endpoint schema configured"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

    resource_types = [DSLResourceTypeWithIncorrectActionType]

    # Defining variables for Authentication Schema
    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value=""),
        CalmVariable.Simple.Secret.string(name="password", value=""),
    ]

    # Defining custom Endpoint Schema
    endpoint_schema = ProviderEndpointSchema(
        type=PROVIDER.ENDPOINT_KIND.CUSTOM,
        variables=[
            CalmVariable.Simple.string(name="server_ip", value="1.1.1.1"),
            CalmVariable.Simple.int(name="port_number", value="443"),
        ],
    )

    # Defining variables for Provider attributes
    variables = [
        CalmVariable.Simple.string(name="provider_var", value="provider_val"),
    ]

    @action
    def Verify():

        """Verify action for Provider"""

        Task.Exec.escript(name="VerifyCreds", filename="scripts/verify_script.py2")

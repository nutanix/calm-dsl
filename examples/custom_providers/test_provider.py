"""
Sample Calm DSL for Hello provider
"""

from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER, RESOURCE_TYPE
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins import (
    CalmVariable,
    CloudProvider,
    action,
    ResourceType,
    ProviderEndpointSchema,
    ProviderTestAccount,
)


class HelloResourceType(ResourceType):
    """Sample ResourceType"""

    # Variables
    variables = [
        CalmVariable.Simple.string(name="resource_type_var", value="value"),
    ]

    # Schemas
    schemas = [
        CalmVariable.Simple.string(name="resource_kind", value="compute"),
    ]

    # Actions
    @action
    def Create(type=RESOURCE_TYPE.ACTION_TYPE.CREATE):
        """Create Action for HelloResourceType"""
        input_var = CalmVariable.Simple.string("default_val", is_mandatory=True)
        outputs = ["output_var"]
        Task.Exec.escript(
            name="Create Resource",
            script="print ('Creating an instance of HelloResourceType');print('@@{input_var}@@')",
        )
        Task.SetVariable.escript(
            name="Set Outputs",
            variables=["output_var"],
            script="print ('output_var = out_val')",
        )
        Task.Exec.escript(name="Verify Outputs", script="print('@@{output_var}@@')")

    @action
    def Delete(type=RESOURCE_TYPE.ACTION_TYPE.DELETE):
        """Delete Action for HelloResourceType"""
        Task.Exec.escript(
            name="Delete Resource",
            script="print ('Deleting an instance of HelloResourceType')",
        )

    @action
    def List(type=RESOURCE_TYPE.ACTION_TYPE.LIST):
        """List Action for HelloResourceType"""
        outputs = ["resource_ids"]
        Task.SetVariable.escript(
            name="List Resources",
            variables=["resource_ids"],
            script="print (\"resource_ids = ['resource1', 'resource2']\")",
        )


class HelloProvider(CloudProvider):
    """Sample provider for Hello"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

    # Resource Types to be managed under this Provider
    resource_types = [HelloResourceType]

    # Authentication Schema
    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value="", is_mandatory=True),
        CalmVariable.Simple.Secret.string(name="password", value="", is_mandatory=True),
    ]

    # Endpoint Schema
    endpoint_schema = ProviderEndpointSchema(
        type=PROVIDER.ENDPOINT_KIND.CUSTOM,
        variables=[
            CalmVariable.Simple.string(
                name="server_ip", value="1.1.1.1", is_mandatory=True
            ),
            CalmVariable.Simple.int(name="port_number", value="443", is_mandatory=True),
        ],
    )

    # Provider attributes
    variables = [
        CalmVariable.Simple.string(name="provider_var", value="provider_val"),
    ]

    test_account = ProviderTestAccount(
        name="TestHelloAccount",
        description="Used for test executions",
        variables=[
            CalmVariable.Simple.string(
                name="server_ip", value="10.10.10.10", is_mandatory=True
            ),
            CalmVariable.Simple.int(
                name="port_number", value="9440", is_mandatory=True
            ),
            CalmVariable.Simple.string(
                name="username", value="root", is_mandatory=True
            ),
            CalmVariable.Simple.Secret.string(
                name="password", value="iamasecret", is_mandatory=True
            ),
        ],
    )

    @action
    def Verify():
        """Verify action for Provider"""
        Task.Exec.escript(name="VerifyCreds", filename="scripts/verify_script.py")
        Task.Exec.escript(
            name="PrintSuccessMessage", script="print ('Successfully Authenticated')"
        )

from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins import (
    CalmVariable,
    CloudProvider,
    action,
    ProviderEndpointSchema,
)


class DslProviderWithVerifyAction(CloudProvider):

    """Sample provider with authentication schema, variables, endpoint schema & verify action configured"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

    # Defining variables for Authentication Schema
    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value=""),
        CalmVariable.Simple.Secret.string(name="password", value=""),
    ]

    # Defining custom Endpoint Schema
    endpoint_schema = ProviderEndpointSchema(
        type=PROVIDER.ENDPOINT_KIND.CUSTOM,
        variables=[
            CalmVariable.Simple.string(name="server_ip", value=""),
            CalmVariable.Simple.int(name="port_number", value=""),
        ],
    )

    # Defining variables for Provider attributes
    variables = [
        CalmVariable.Simple.string(name="provider_var", value=""),
    ]

    @action
    def Verify():  # Name of the action must be 'Verify'

        """Verify action for Provider"""

        Task.Exec.escript(name="VerifyCreds", filename="scripts/verify_script.py2")

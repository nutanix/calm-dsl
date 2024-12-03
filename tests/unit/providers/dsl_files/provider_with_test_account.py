from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins import (
    CalmVariable,
    CloudProvider,
    action,
    ProviderEndpointSchema,
    ProviderTestAccount,
)


class HelloProvider(CloudProvider):
    """Sample provider for Hello"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value="", is_mandatory=True),
        CalmVariable.Simple.Secret.string(name="password", value="", is_mandatory=True),
    ]

    endpoint_schema = ProviderEndpointSchema(
        type=PROVIDER.ENDPOINT_KIND.CUSTOM,
        variables=[
            CalmVariable.Simple.string(
                name="server_ip", value="1.1.1.1", is_mandatory=True
            ),
            CalmVariable.Simple.int(name="port_number", value="443", is_mandatory=True),
        ],
    )

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

        Task.Exec.escript(name="VerifyCreds", filename="scripts/verify_script.py2")

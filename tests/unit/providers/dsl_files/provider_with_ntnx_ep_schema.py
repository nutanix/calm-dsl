from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.builtins import CalmVariable, CloudProvider
from calm.dsl.builtins import NutanixEndpointSchema


class DslProviderWithNtnxEPSchema(CloudProvider):

    """Sample provider with authentication schema, variables & 'ntnx' endpoint schema configured"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

    # Defining variables for Authentication Schema
    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value=""),
        CalmVariable.Simple.Secret.string(name="password", value=""),
    ]

    # Nutanix Endpoint Schema
    endpoint_schema = NutanixEndpointSchema()

    # Defining variables for Provider attributes
    variables = [
        CalmVariable.Simple.string(name="provider_var", value="provider_val"),
    ]

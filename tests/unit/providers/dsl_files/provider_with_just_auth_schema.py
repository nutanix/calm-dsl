from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.builtins import CalmVariable, CloudProvider


class DslProviderWithJustAuthSchema(CloudProvider):

    """Sample provider with just authentication schema configured"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

    # Defining variables for Authentication Schema
    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value=""),
        CalmVariable.Simple.Secret.string(name="password", value=""),
    ]

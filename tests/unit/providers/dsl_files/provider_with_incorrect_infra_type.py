from calm.dsl.builtins import CloudProvider, CalmVariable


class DslProviderWithIncorrectInfraType(CloudProvider):

    """Sample provider with authentication schema, variables & custom endpoint schema configured"""

    infra_type = "notexpected"

    # Defining variables for Authentication Schema
    auth_schema_variables = [
        CalmVariable.Simple.string(name="username", value=""),
        CalmVariable.Simple.Secret.string(name="password", value=""),
    ]

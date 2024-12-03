from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER
from calm.dsl.builtins import CloudProvider


class DslProviderWithNoAuthSchema(CloudProvider):

    """Sample provider with NO authentication schema configured"""

    infra_type = PROVIDER.INFRA_TYPE.CLOUD

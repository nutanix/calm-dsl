from .resource import ResourceAPI


class AppProtectionPolicyAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(
            connection, resource_type="app_protection_policies", calm_api=True
        )

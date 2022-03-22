from .resource import ResourceAPI


class ProviderAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="providers", calm_api=True)

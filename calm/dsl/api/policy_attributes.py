from .resource import ResourceAPI


class PolicyAttributesAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="policy_attributes", calm_api=True)

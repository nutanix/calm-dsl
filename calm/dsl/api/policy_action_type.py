from .resource import ResourceAPI
from .connection import REQUEST


class PolicyActionTypeAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="policy_action_types", calm_api=True)

from .resource import ResourceAPI
from .connection import REQUEST


class PolicyEventAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="policy_events", calm_api=True)

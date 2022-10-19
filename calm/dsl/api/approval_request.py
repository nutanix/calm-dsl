from .resource import ResourceAPI


class ApprovalRequestAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="approval_requests", calm_api=True)

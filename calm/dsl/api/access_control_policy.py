from .resource import ResourceAPI


class AccessControlPolicyAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="access_control_policies")

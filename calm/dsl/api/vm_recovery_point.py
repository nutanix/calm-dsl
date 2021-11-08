from .resource import ResourceAPI


class VmRecoveryPointAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="nutanix/v1/vm_recovery_points")

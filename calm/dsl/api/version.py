from .resource import ResourceAPI
from .connection import REQUEST


class VersionAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="")

        self.CALM_VERSION = "apps/version"
        self.PC_VERSION = self.ROOT + "/prism_central"

    def get_calm_version(self):
        return self.connection._call(
            self.CALM_VERSION, verify=False, method=REQUEST.METHOD.GET,
        )

    def get_pc_version(self):
        return self.connection._call(
            self.PC_VERSION,
            verify=False,
            method=REQUEST.METHOD.GET,
        )

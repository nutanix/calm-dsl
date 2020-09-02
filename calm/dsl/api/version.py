from .connection import REQUEST


class VersionAPI:
    def __init__(self, connection):
        self.connection = connection

        self.calm_version = "apps/version"
        self.pc_version = "PrismGateway/services/rest/v1/cluster/version"

    def get_calm_version(self):
        return self.connection._call(
            self.calm_version, verify=False, method=REQUEST.METHOD.GET
        )

    def get_pc_version(self):
        return self.connection._call(
            self.pc_version,
            verify=False,
            method=REQUEST.METHOD.GET,
            ignore_error=True,
            warning_msg="Could not get PC Version",
        )

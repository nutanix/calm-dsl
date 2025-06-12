from .connection import REQUEST, MultiConnection
from calm.dsl.constants import MULTICONNECT


class VersionAPI:
    def __init__(self, connection):
        self.connection = connection

        # If multi connection object is supplied it will return connection.pc_conn_obj because VersionAPI's are routed to PC.
        if isinstance(connection, MultiConnection):
            self.connection = getattr(connection, MULTICONNECT.PC_OBJ)

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

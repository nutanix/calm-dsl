from calm.dsl.config import get_config

from .connection import get_connection, update_connection, REQUEST
from .blueprint import BlueprintAPI
from .application import ApplicationAPI
from .project import ProjectAPI
from .setting import SettingAPI


class ClientHandle:
    def __init__(self, connection):
        self.connection = connection

    def _connect(self):

        self.connection.connect()

        # Note - add entity api classes here
        self.project = ProjectAPI(self.connection)
        self.blueprint = BlueprintAPI(self.connection)
        self.application = ApplicationAPI(self.connection)
        self.account = SettingAPI(self.connection)


_CLIENT_HANDLE = None


def get_client_handle(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    global _CLIENT_HANDLE
    if not _CLIENT_HANDLE:
        update_client_handle(host, port, auth_type, scheme, auth)
    return _CLIENT_HANDLE


def update_client_handle(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    global _CLIENT_HANDLE
    update_connection(host, port, auth_type, scheme=scheme, auth=auth)
    connection = get_connection(host, port, auth_type, scheme, auth)
    _CLIENT_HANDLE = ClientHandle(connection)
    _CLIENT_HANDLE._connect()


def get_api_client():

    config = get_config()

    pc_ip = config["SERVER"].get("pc_ip")
    pc_port = config["SERVER"].get("pc_port")
    username = config["SERVER"].get("pc_username")
    password = config["SERVER"].get("pc_password")

    return get_client_handle(pc_ip, pc_port, auth=(username, password))

from calm.dsl.config import get_config

from .connection import get_connection, update_connection, REQUEST, Connection
from .blueprint import BlueprintAPI
from .application import ApplicationAPI
from .project import ProjectAPI
from .setting import SettingAPI
from .marketplace import MarketPlaceAPI
from .app_icons import AppIconAPI
from .version import VersionAPI
from .showback import ShowbackAPI
from .user import UserAPI
from .user_group import UserGroupAPI
from .role import RoleAPI
from .directory_service import DirectoryServiceAPI


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
        self.market_place = MarketPlaceAPI(self.connection)
        self.app_icon = AppIconAPI(self.connection)
        self.version = VersionAPI(self.connection)
        self.showback = ShowbackAPI(self.connection)
        self.user = UserAPI(self.connection)
        self.group = UserGroupAPI(self.connection)
        self.role = RoleAPI(self.connection)
        self.directory_service = DirectoryServiceAPI(self.connection)


_CLIENT_HANDLE = None


def get_client_handle(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
    temp=False,  # This flag is used to generate temp handle
):
    global _CLIENT_HANDLE
    if temp:
        connection = Connection(host, port, auth_type, scheme, auth)
        handle = ClientHandle(connection)
        handle._connect()
        return handle

    else:
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
    return _CLIENT_HANDLE


def get_api_client():

    config = get_config()

    pc_ip = config["SERVER"].get("pc_ip")
    pc_port = config["SERVER"].get("pc_port")
    username = config["SERVER"].get("pc_username")
    password = config["SERVER"].get("pc_password")

    return get_client_handle(pc_ip, pc_port, auth=(username, password))

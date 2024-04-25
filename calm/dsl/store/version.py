import peewee

from calm.dsl.db import get_db_handle
from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.db.table_config import VersionTable
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class Version:
    """Version class Implementation"""

    @classmethod
    def create(cls, name="", pc_ip="", version=""):
        """Store the uuid of entity in cache"""

        db = get_db_handle()
        db.version_table.create(name=name, pc_ip=pc_ip, version=version)

    @classmethod
    def get_version(cls, name):
        """Returns the version of entity present"""

        db_handle = get_db_handle()
        try:
            entity = db_handle.version_table.get(db_handle.version_table.name == name)
            return entity.version

        except (peewee.OperationalError, peewee.DoesNotExist):
            return None

    @classmethod
    def get_version_data(cls, name):
        """Returns the data stored in version cache for name supplied"""

        db = get_db_handle()
        try:
            entity = db.version_table.get_entity_data(name)
            return entity
        except:
            return {}

    @classmethod
    def sync(cls):
        try:
            db = get_db_handle()
            db.version_table.clear()

            client = get_api_client()
            ContextObj = get_context()
            server_config = ContextObj.get_server_config()
            pc_ip = server_config["pc_ip"]

            # Update calm version
            res, err = client.version.get_calm_version()
            calm_version = res.content.decode("utf-8")
            cls.create("Calm", pc_ip, calm_version)

            # Update pc_version of PC(if host exist)
            res, err = client.version.get_pc_version()
            if not err:
                res = res.json()
                pc_version = res["version"]
                cls.create("PC", pc_ip, pc_version)

        except (peewee.OperationalError, peewee.IntegrityError):
            db_handle = get_db_handle()
            db_handle.db.drop_tables([VersionTable])
            db_handle.db.create_tables([VersionTable])
            cls.sync()

    @classmethod
    def get_cache_type(cls):
        return "Version"

import atexit
import os

from calm.dsl.config import get_context
from .table_config import dsl_database, SecretTable, DataTable, VersionTable
from .table_config import CacheTableBase
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class Database:
    """DSL database connection"""

    db = None
    registered_tables = []

    @classmethod
    def update_db(cls, db_instance):
        cls.db = db_instance

    @staticmethod
    def instantiate_db():
        ContextObj = get_context()
        init_obj = ContextObj.get_init_config()
        db_location = init_obj["DB"]["location"]
        dsl_database.init(db_location)
        return dsl_database

    def __init__(self):
        self.update_db(self.instantiate_db())
        self.connect()
        self.secret_table = self.set_and_verify(SecretTable)
        self.data_table = self.set_and_verify(DataTable)
        self.version_table = self.set_and_verify(VersionTable)

        for table_type, table in CacheTableBase.tables.items():
            setattr(self, table_type, self.set_and_verify(table))

    def set_and_verify(self, table_cls):
        """Verify whether this class exists in db
        If not, then creates one
        """

        if not self.db.table_exists((table_cls.__name__).lower()):
            self.db.create_tables([table_cls])

        # Register table to class
        if table_cls not in self.registered_tables:
            self.registered_tables.append(table_cls)

        return table_cls

    def is_closed(self):
        """return True if db connection is closed else False"""

        if self.db:
            return self.db.is_closed()

        # If db not found, return true
        return True

    def connect(self):

        LOG.debug("Connecting to local DB")
        self.db.connect()
        atexit.register(self.close)

    def close(self):

        LOG.debug("Closing connection to local DB")
        self.db.close()


_Database = None


def get_db_handle():
    """Returns the db handle"""

    global _Database
    if not _Database:
        _Database = Database()

    return _Database


def init_db_handle():
    """Initializes database module and replaces the existing one"""

    global _Database

    try:
        # Closing existing connection if exists
        if not _Database.is_closed():
            # Unregister close() method from atexit handler
            atexit.unregister(_Database.close)

            # Close the connection
            _Database.close()

    except:  # noqa
        pass

    # Removing existing db at init location if exists
    ContextObj = get_context()
    init_obj = ContextObj.get_init_config()
    db_location = init_obj["DB"]["location"]
    if os.path.exists(db_location):
        os.remove(db_location)

    # Initialize new database object
    _Database = Database()

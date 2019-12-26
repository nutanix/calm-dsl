import traceback

from calm.dsl.config import get_db_location

from .table_config import dsl_database, SecretTable, DataTable, CacheTable


class Database:
    """DSL database connection"""

    db = None

    @classmethod
    def update_db(cls, db_instance):
        cls.db = db_instance

    @staticmethod
    def instantiate_db():
        db_location = get_db_location()
        dsl_database.init(db_location)
        return dsl_database

    def __init__(self):
        if not self.db:
            self.update_db(self.instantiate_db())

        self.secret_table = self.set_and_verify(SecretTable)
        self.data_table = self.set_and_verify(DataTable)
        self.cache_table = self.set_and_verify(CacheTable)

    def set_and_verify(self, table_cls):
        """ Verify whether this class exists in db
            If not, then creates one
        """

        if self.db.is_closed():
            self.db.connect()
        if not self.db.table_exists((table_cls.__name__).lower()):
            self.db.create_tables([table_cls])

        self.db.close()
        return table_cls

    def __enter__(self):

        if self.db.is_closed():
            self.db.connect()

        return self

    def __exit__(self, exc_type, exc_value, tb):

        if not self.db.is_closed():
            self.db.close()

        if exc_type:
            # If ValueError is raised, don't print Exception
            # forwarding it further for catching
            if exc_type.__name__ == "ValueError":
                raise exc_type(exc_value)

            else:
                traceback.print_exception(exc_type, exc_value, tb)

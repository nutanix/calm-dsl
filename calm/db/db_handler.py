from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    BlobField,
    DateTimeField,
    ForeignKeyField,
)

import os
import datetime
import traceback

db_location = "calm/db/dsl.db"
db_location = os.path.abspath(db_location)

# Creating a database file if not exists
if not os.path.exists(db_location):
    with open(db_location, "w"):
        pass

# Initialization of database
dsl_db = SqliteDatabase(db_location)


class BaseModel(Model):
    class Meta:
        database = dsl_db


class SecretTable(BaseModel):
    name = CharField(primary_key=True)
    uuid = CharField()
    creation_time = DateTimeField(default=datetime.datetime.now())
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "creation_time": self.creation_time,
            "last_update_time": self.last_update_time,
        }


class DataTable(BaseModel):
    secret_ref = ForeignKeyField(SecretTable, backref="data")
    kdf_salt = BlobField()
    ciphertext = BlobField()
    iv = BlobField()
    auth_tag = BlobField()
    pass_phrase = BlobField()

    def generate_enc_msg(self):
        return (self.kdf_salt, self.ciphertext, self.iv, self.auth_tag)


# checking for availabilty of tables
dsl_db.connect()
if not dsl_db.table_exists((SecretTable.__name__).lower()):
    dsl_db.create_tables([SecretTable])

if not dsl_db.table_exists((DataTable.__name__).lower()):
    dsl_db.create_tables([DataTable])

dsl_db.close()


class Database:
    """DSL database connection"""

    def __init__(self):

        self.db = dsl_db
        self.secret_table = SecretTable
        self.data_table = DataTable

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

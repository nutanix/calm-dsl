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
import uuid

from .crypto import Crypto

db_location = "calm/db/dsl.db"
db_location = os.path.abspath(db_location)
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
            "last_update_time": self.last_update_time
        }


class DataTable(BaseModel):
    secret_ref = ForeignKeyField(SecretTable, backref="data")
    kdf_salt = BlobField()
    ciphertext = BlobField()
    iv = BlobField()
    auth_tag = BlobField()
    pass_phrase = BlobField()
    uuid = CharField()
    creation_time = DateTimeField(default=datetime.datetime.now())
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def generate_enc_msg(self):
        return (self.kdf_salt, self.ciphertext, self.iv, self.auth_tag)


class Secret:

    db = dsl_db
    secret_table = SecretTable
    data_table = DataTable

    @classmethod
    def connect(cls):
        """
           Establishes the connection for db access
           Creates the table in db if not exists
        """

        if cls.db.is_closed():
            cls.db.connect()

        if not cls.db.table_exists((cls.secret_table.__name__).lower()):
            cls.db.create_tables([cls.secret_table])

        if not cls.db.table_exists((cls.secret_table.__name__).lower()):
            cls.db.create_tables([cls.secret_table])

    @classmethod
    def close(cls):
        """Closes the connection"""

        if not cls.db.is_closed():
            cls.db.close()

    @classmethod
    def create(cls, name, value, pass_phrase):
        """Stores the secret in db"""

        cls.connect()

        if not pass_phrase:
            pass_phrase = b"dslp4ssw0rd"  # TODO Replace by random

        else:
            pass_phrase = pass_phrase.encode()

        encrypted_msg = Crypto.encrypt_AES_GCM(value, pass_phrase)
        (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

        secret = cls.secret_table.create(name=name, uuid=str(uuid.uuid4()))

        cls.data_table.create(
            secret_ref=secret,
            kdf_salt=kdf_salt,
            ciphertext=ciphertext,
            iv=iv,
            auth_tag=auth_tag,
            pass_phrase=pass_phrase,
        )

        cls.close()

    @classmethod
    def get_instance(cls, name):
        """Return secret instance"""

        was_closed = False

        # If not closed already, do not close on function exit
        if cls.db.is_closed():
            cls.connect()
            was_closed = True

        secret = cls.secret_table.get(cls.secret_table.name == name)

        if was_closed:
            cls.close()

        return secret

    @classmethod
    def delete(cls, name):
        """Deletes the secret from db"""

        cls.connect()
        secret = cls.get_instance(name)
        for secret_data in secret.data:
            secret_data.delete_instance()  # deleting its data

        secret.delete_instance()  # deleting that secret

        cls.close()

    @classmethod
    def update(cls, name, value, pass_phrase):
        """Updates the secret in Database"""

        cls.connect()
        secret = cls.get_instance(name)
        secret_data = secret.data[0]    # using backref

        if not pass_phrase:
            pass_phrase = secret_data.pass_phrase
        else:
            pass_phrase = pass_phrase.encode()

        encrypted_msg = Crypto.encrypt_AES_GCM(value, pass_phrase)
        (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

        query = cls.data_table.update(
            kdf_salt=kdf_salt,
            ciphertext=ciphertext,
            iv=iv,
            auth_tag=auth_tag,
            pass_phrase=pass_phrase,
        ).where(cls.data_table.secret_ref == secret)

        query.execute()

        query = cls.secret_table.update(last_update_time=datetime.datetime.now()).where(
            cls.secret_table.name == name
        )

        query.execute()

        cls.close()

    @classmethod
    def list(cls):
        """returns the Secret object"""

        cls.connect()
        secret_basic_configs = []

        for secret in cls.secret_table.select():
            secret_basic_configs.append(secret.get_detail_dict())

        cls.close()
        return secret_basic_configs

    @classmethod
    def find(cls, name, pass_phrase=None):
        """Find the value of secret"""

        cls.connect()
        secret = cls.get_instance(name)
        secret_data = secret.data[0]  # using backref

        if not pass_phrase:
            pass_phrase = secret_data.pass_phrase  # TODO Replace by random
        else:
            pass_phrase = pass_phrase.encode()

        enc_msg = secret_data.generate_enc_msg()
        secret_val = Crypto.decrypt_AES_GCM(enc_msg, pass_phrase)
        secret_val = secret_val.decode("utf8")

        cls.close()

        return secret_val

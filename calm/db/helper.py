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

from .crypto import encrypt_AES_GCM, decrypt_AES_GCM

db_location = "calm/db/dsl.db"
db_location = os.path.abspath(db_location)

db = SqliteDatabase(db_location)
db.connect()


class BaseModel(Model):
    class Meta:
        database = db


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

    def generate_enc_msg(self):
        return (self.kdf_salt, self.ciphertext, self.iv, self.auth_tag)


if not db.table_exists((SecretTable.__name__).lower()):
    db.create_tables([SecretTable])

if not db.table_exists((DataTable.__name__).lower()):
    db.create_tables([DataTable])

db.close()


def _create_secret(name, value, pass_phrase):
    """Stores the secret in db"""

    db.connect()

    if not pass_phrase:
        pass_phrase = b"dslp4ssw0rd"  # TODO Replace by random

    else:
        pass_phrase = pass_phrase.encode()

    encrypted_msg = encrypt_AES_GCM(value, pass_phrase)
    (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

    secret = SecretTable.create(name=name, uuid=str(uuid.uuid4()))

    DataTable.create(
        secret_ref=secret,
        kdf_salt=kdf_salt,
        ciphertext=ciphertext,
        iv=iv,
        auth_tag=auth_tag,
        pass_phrase=pass_phrase,
    )

    db.close()


def _delete_secret(name):
    """Deletes the secret from db"""

    db.connect()
    secret = get_secret(name)
    for secret_data in secret.data:
        secret_data.delete_instance()  # deleting its data

    secret.delete_instance()  # deleting that secret

    db.close()


def get_secret(name):
    """Return secret instance"""

    was_closed = False
    if db.is_closed():
        db.connect()
        was_closed = True

    secret = SecretTable.get(SecretTable.name == name)

    if was_closed:
        db.close()

    return secret


def _update_secret(name, value, pass_phrase):
    """Updates the secret in Database"""

    db.connect()
    secret = get_secret(name)
    secret_data = secret.data[0]    # using backref

    if not pass_phrase:
        pass_phrase = secret_data.pass_phrase
    else:
        pass_phrase = pass_phrase.encode()

    encrypted_msg = encrypt_AES_GCM(value, pass_phrase)
    (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

    query = DataTable.update(
        kdf_salt=kdf_salt,
        ciphertext=ciphertext,
        iv=iv,
        auth_tag=auth_tag,
        pass_phrase=pass_phrase,
    ).where(DataTable.secret_ref == secret)

    query.execute()

    query = SecretTable.update(last_update_time=datetime.datetime.now()).where(
        SecretTable.name == name
    )

    query.execute()

    db.close()


def list_secrets():
    """returns the Secret object"""

    db.connect()
    secret_basic_configs = []

    for secret in SecretTable.select():
        secret_basic_configs.append(secret.get_detail_dict())

    db.close()
    return secret_basic_configs


def _find_secret(name, pass_phrase=None):
    """Find the value of secret"""

    db.connect()
    secret = get_secret(name)
    secret_data = secret.data[0]  # using backref

    if not pass_phrase:
        pass_phrase = secret_data.pass_phrase  # TODO Replace by random
    else:
        pass_phrase = pass_phrase.encode()

    enc_msg = secret_data.generate_enc_msg()
    secret_val = decrypt_AES_GCM(enc_msg, pass_phrase)

    secret_val = secret_val.decode("utf8")

    db.close()

    return secret_val


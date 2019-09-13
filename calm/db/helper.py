from peewee import SqliteDatabase, Model, CharField, BlobField
import os

from .crypto import encrypt_AES_GCM, decrypt_AES_GCM


db_location = "calm/db/dsl.db"
db_location = os.path.abspath(db_location)

db = SqliteDatabase(db_location)
db.connect()


class Secret(Model):
    name = CharField()
    kdf_salt = BlobField()
    ciphertext = BlobField()
    iv = BlobField()
    auth_tag = BlobField()
    pass_phrase = BlobField()

    def generate_enc_msg(self):
        return (self.kdf_salt, self.ciphertext, self.iv, self.auth_tag) 

    class Meta:
        database = db


if not db.table_exists((Secret.__name__).lower()):
    db.create_tables([Secret])

db.close()


def _create_secret(name, value, pass_phrase):

    db.connect()

    if not pass_phrase:
        pass_phrase = b"dslp4ssw0rd"  # TODO Replace by random

    else:
        pass_phrase = pass_phrase.encode()

    encrypted_msg = encrypt_AES_GCM(value, pass_phrase)
    (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

    secret = Secret.create(
        name=name,
        kdf_salt=kdf_salt,
        ciphertext=ciphertext,
        iv=iv,
        auth_tag=auth_tag,
        pass_phrase=pass_phrase,
    )
    import pdb
    pdb.set_trace()

    secret.save()
    db.close()


def _delete_secret(name):

    db.connect()
    secret = get_secret(name)
    secret.delete_instance()
    db.close()


def get_secret(name):

    was_closed = False
    if db.is_closed():
        db.connect()
        was_closed = True
    secret = Secret.get(Secret.name == name)

    if was_closed:
        db.close()

    return secret


def _update_secret(name, value, pass_phrase):

    db.connect()
    secret = get_secret(name)

    if not pass_phrase:
        pass_phrase = secret.pass_phrase

    else:
        pass_phrase = pass_phrase.encode()

    encrypted_msg = encrypt_AES_GCM(value, pass_phrase)
    (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

    query = Secret.update(
        kdf_salt=kdf_salt,
        ciphertext=ciphertext,
        iv=iv,
        auth_tag=auth_tag,
        pass_phrase=pass_phrase,
    ).where(Secret.name == name)

    query.execute()
    db.close()


def list_secrets():

    db.connect()
    secrets = []
    for secret in Secret.select():
        secrets.append(secret.name)

    db.close()
    return secrets


def _find_secret(name, pass_phrase=None):

    db.connect()
    secret = get_secret(name)

    if not pass_phrase:
        pass_phrase = secret.pass_phrase  # TODO Replace by random

    else:
        pass_phrase = pass_phrase.encode()

    enc_msg = secret.generate_enc_msg()
    secret_val = decrypt_AES_GCM(enc_msg, pass_phrase)

    secret_val = secret_val.decode("utf8")
    db.close()

    return secret_val

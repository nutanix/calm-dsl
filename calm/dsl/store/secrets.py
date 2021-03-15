import datetime
import uuid
import peewee

from ..crypto import Crypto
from calm.dsl.db import get_db_handle
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class Secret:
    """Secret class implementation"""

    @classmethod
    def create(cls, name, value, pass_phrase="dslp4ssw0rd"):
        """Stores the secret in db"""

        db = get_db_handle()
        pass_phrase = pass_phrase.encode()
        LOG.debug("Encryting data")
        encrypted_msg = Crypto.encrypt_AES_GCM(value, pass_phrase)

        (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

        secret = db.secret_table.create(name=name, uuid=str(uuid.uuid4()))

        db.data_table.create(
            secret_ref=secret,
            kdf_salt=kdf_salt,
            ciphertext=ciphertext,
            iv=iv,
            auth_tag=auth_tag,
            pass_phrase=pass_phrase,
        )

    @classmethod
    def get_instance(cls, name):
        """Return secret instance"""

        db = get_db_handle()
        try:
            secret = db.secret_table.get(db.secret_table.name == name)
        except peewee.DoesNotExist:
            raise ValueError("Entity not found !!!")

        return secret

    @classmethod
    def delete(cls, name):
        """Deletes the secret from db"""

        secret = cls.get_instance(name)
        secret.delete_instance(recursive=True)

    @classmethod
    def update(cls, name, value):
        """Updates the secret in Database"""

        db = get_db_handle()
        secret = cls.get_instance(name)
        secret_data = secret.data[0]  # using backref

        pass_phrase = secret_data.pass_phrase

        LOG.debug("Encrypting new data")
        encrypted_msg = Crypto.encrypt_AES_GCM(value, pass_phrase)

        (kdf_salt, ciphertext, iv, auth_tag) = encrypted_msg

        query = db.data_table.update(
            kdf_salt=kdf_salt,
            ciphertext=ciphertext,
            iv=iv,
            auth_tag=auth_tag,
            pass_phrase=pass_phrase,
        ).where(db.data_table.secret_ref == secret)

        query.execute()

        query = db.secret_table.update(last_update_time=datetime.datetime.now()).where(
            db.secret_table.name == name
        )

        query.execute()

    @classmethod
    def list(cls):
        """returns the list of secrets stored in db"""

        db = get_db_handle()

        secret_basic_configs = []
        for secret in db.secret_table.select():
            secret_basic_configs.append(secret.get_detail_dict())

        return secret_basic_configs

    @classmethod
    def find(cls, name, pass_phrase=None):
        """Find the value of secret"""

        secret = cls.get_instance(name)
        secret_data = secret.data[0]  # using backref

        if not pass_phrase:
            pass_phrase = secret_data.pass_phrase
        else:
            pass_phrase = pass_phrase.encode()

        enc_msg = secret_data.generate_enc_msg()
        LOG.debug("Decrypting data")
        secret_val = Crypto.decrypt_AES_GCM(enc_msg, pass_phrase)

        return secret_val

    @classmethod
    def clear(cls):
        """Deletes all the secrets present in the data"""

        db = get_db_handle()
        for secret in db.secret_table.select():
            secret.delete_instance(recursive=True)

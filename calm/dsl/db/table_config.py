from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    BlobField,
    DateTimeField,
    ForeignKeyField,
    CompositeKey,
)
import datetime

# Proxy database
dsl_database = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = dsl_database


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


class CacheTable(BaseModel):
    entity_type = CharField()
    entity_name = CharField()
    entity_uuid = CharField()
    entity_list_api_suffix = CharField()
    last_update_time = DateTimeField(default=datetime.datetime.now())

    def get_detail_dict(self):
        return {
            "type": self.entity_type,
            "name": self.entity_name,
            "uuid": self.entity_uuid,
            "last_update_time": self.last_update_time,
        }

    class Meta:
        database = dsl_database
        primary_key = CompositeKey("entity_type", "entity_name")

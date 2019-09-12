from peewee import SqliteDatabase, Model, CharField
import os


db_location = "calm/db/dsl.db"
db_location = os.path.abspath(db_location)

db = SqliteDatabase(db_location)
db.connect()


class Secret(Model):
    name = CharField()
    value = CharField()

    class Meta:
        database = db


if not db.table_exists((Secret.__name__).lower()):
    db.create_tables([Secret])

db.close()


def _create_secret(name, value):

    db.connect()
    secret = Secret.create(name=name, value=value)
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


def _update_secret(name, value):

    db.connect()
    secret = get_secret(name)
    secret.value = value
    secret.save()
    db.close()


def list_secrets():

    db.connect()
    secrets = []
    for secret in Secret.select():
        secrets.append(secret.name)

    db.close()
    return secrets

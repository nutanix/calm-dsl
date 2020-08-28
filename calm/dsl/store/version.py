import peewee

from calm.dsl.db import get_db_handle
from calm.dsl.api import get_api_client


class Version:
    """Version class Implementation"""

    @classmethod
    def create(cls, name="", version=""):
        """Store the uuid of entity in cache"""

        db = get_db_handle()
        db.version_table.create(name=name, version=version)

    @classmethod
    def get_version(cls, name):
        """Returns the version of entity present"""

        db = get_db_handle()
        try:
            entity = db.version_table.get(db.version_table.name == name)
            return entity.version

        except peewee.DoesNotExist:
            return None

    @classmethod
    def sync(cls):

        db = get_db_handle()
        for entity in db.version_table.select():
            query = db.version_table.delete().where(
                db.version_table.name == entity.name
            )
            query.execute()

        client = get_api_client()

        # Update calm version
        res, err = client.version.get_calm_version()
        calm_version = res.content.decode("utf-8")
        cls.create("Calm", calm_version)

        # Update pc_version of PC(if host exist)
        res, err = client.version.get_pc_version()
        if not err:
            res = res.json()
            pc_version = res["version"]
            cls.create("PC", pc_version)

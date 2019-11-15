import peewee
from ..db import Database
from calm.dsl.api import get_resource_api, get_api_client
import click


class Cache:
    """Cache class Implementation"""

    # TODO move this mapping to constants(api may change)
    entity_type_api_map = {"AHV_DISK_IMAGE": "images", "AHV_SUBNETS": "subnets"}

    @classmethod
    def create(cls, entity_type="", entity_name="", entity_uuid=""):
        """Store the uuid of entity in cache"""

        with Database() as db:

            db.cache_table.create(
                entity_type=entity_type,
                entity_name=entity_name,
                entity_uuid=entity_uuid,
                entity_list_api_suffix=cls.entity_type_api_map[entity_type],
            )

    @classmethod
    def get_entity_uuid(cls, entity_type, entity_name):
        """Returns the uuid of entity present"""

        with Database() as db:

            try:
                entity = db.cache_table.get(
                    db.cache_table.entity_type == entity_type
                    and db.cache_table.entity_name == entity_name
                )

                return entity.entity_uuid

            except peewee.DoesNotExist:
                # Store the the entity_details in the cache
                cls.create(entity_type=entity_type, entity_name=entity_name)
                return ""

    @classmethod
    def sync(cls):
        """Sync with the api of corresponding entities"""

        with Database() as db:
            client = get_api_client()

            for db_entity in db.cache_table.select():
                name = db_entity.entity_name
                api_suffix = db_entity.entity_list_api_suffix
                Obj = get_resource_api(api_suffix, client.connection)

                res = Obj.get_name_uuid_map()
                entity_uuid = res.get(name, None)

                if not entity_uuid:
                    click.echo("\nEntity {} not found".format(name))

                db_entity.entity_uuid = entity_uuid
                db_entity.save()

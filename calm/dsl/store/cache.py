import peewee
import datetime
import warnings

from ..db import Database
from calm.dsl.api import get_resource_api, get_api_client
import click


class Cache:
    """Cache class Implementation"""

    # TODO move this mapping to constants(api may change)
    entity_type_api_map = {
        "AHV_DISK_IMAGE": "images",
        "AHV_SUBNETS": "subnets",
        "AHV_NETWORK_FUNCTION_CHAIN": "network_function_chains",
        "PROJECT": "projects"
    }

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
    def update_entities(cls):
        """Sync with the api of corresponding entities"""

        with Database() as db:
            client = get_api_client()

            invalid_entities = []
            for db_entity in db.cache_table.select():
                name = db_entity.entity_name
                api_suffix = db_entity.entity_list_api_suffix
                Obj = get_resource_api(api_suffix, client.connection)

                try:
                    res = Obj.get_name_uuid_map()
                except Exception:
                    pc_ip = client.connection.host
                    warnings.warn(
                        UserWarning("Cannot fetch data from {}".format(pc_ip))
                    )
                    return

                entity_uuid = res.get(name, None)
                if not entity_uuid:
                    entity_type = db_entity.entity_type
                    invalid_entities.append((entity_type, name))
                    db_entity.delete_instance()  # Deleting entity if not found
                    continue

                db_entity.entity_uuid = entity_uuid
                db_entity.last_update_time = datetime.datetime.now()
                db_entity.save()

            if invalid_entities:
                error = ""
                for entity in invalid_entities:
                    click.secho(
                        "- Entity {} of type {} not found".format(entity[1], entity[0]),
                        fg="red",
                    )
                    error += "\n- Entity {} of type {} not found".format(
                        entity[1], entity[0]
                    )
                raise Exception(error)

    @classmethod
    def clear_entities(cls):
        """Deletes all the data present in the cache"""

        with Database() as db:
            for db_entity in db.cache_table.select():
                db_entity.delete_instance()

    @classmethod
    def delete_entity(cls, entity_type, entity_name):
        """Deletes data corresponding to enity present in the cache"""

        with Database() as db:
            entity = db.cache_table.get(
                db.cache_table.entity_type == entity_type
                and db.cache_table.entity_name == entity_name
            )

            entity.delete_instance()

    @classmethod
    def list(cls):
        """return the list of entities stored in db"""

        with Database() as db:

            cache_data = []
            for entity in db.cache_table.select():
                cache_data.append(entity.get_detail_dict())

            return cache_data

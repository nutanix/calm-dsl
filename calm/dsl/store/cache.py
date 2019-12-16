import peewee
import warnings

from ..db import Database
from calm.dsl.api import get_resource_api, get_api_client


class Cache:
    """Cache class Implementation"""

    # TODO move this mapping to constants(api may change)
    entity_type_api_map = {
        "AHV_DISK_IMAGE": "images",
        "AHV_SUBNET": "subnets",
        "AHV_NETWORK_FUNCTION_CHAIN": "network_function_chains",
        "PROJECT": "projects",
    }

    @classmethod
    def get_entity_types(cls):
        """Entity types used in the cache"""
        return list(cls.entity_type_api_map.keys())

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
                return None

    @classmethod
    def sync(cls, entity_type=None):

        updating_entity_types = []

        if entity_type:
            if entity_type not in list(cls.entity_type_api_map.keys()):
                raise ValueError("Entity type {} not registered". format(entity_type))

            updating_entity_types.append(entity_type)

        else:
            updating_entity_types.extend(list(cls.entity_type_api_map.keys()))

        with Database() as db:

            for entity_type in updating_entity_types:
                query = db.cache_table.delete().where(db.cache_table.entity_type == entity_type)
                query.execute()

            client = get_api_client()

            for entity_type in updating_entity_types:
                api_suffix = cls.entity_type_api_map[entity_type]
                Obj = get_resource_api(api_suffix, client.connection)
                try:
                    res = Obj.get_name_uuid_map()
                    for name, uuid in res.items():
                        cls.create(entity_type=entity_type, entity_name=name, entity_uuid=uuid)
                except Exception:
                    pc_ip = client.connection.host
                    warnings.warn(
                        UserWarning("Cannot fetch data from {}".format(pc_ip))
                    )

    @classmethod
    def clear_entities(cls):
        """Deletes all the data present in the cache"""

        with Database() as db:
            for db_entity in db.cache_table.select():
                db_entity.delete_instance()

    @classmethod
    def list(cls):
        """return the list of entities stored in db"""

        with Database() as db:

            cache_data = []
            for entity in db.cache_table.select():
                cache_data.append(entity.get_detail_dict())

            return cache_data

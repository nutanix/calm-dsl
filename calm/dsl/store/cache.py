import peewee

from ..db import get_db_handle
from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


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

        db = get_db_handle()
        db.cache_table.create(
            entity_type=entity_type,
            entity_name=entity_name,
            entity_uuid=entity_uuid,
            entity_list_api_suffix=cls.entity_type_api_map[entity_type],
        )

    @classmethod
    def get_entity_uuid(cls, entity_type, entity_name):
        """Returns the uuid of entity present"""

        db = get_db_handle()
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
            if entity_type not in cls.get_entity_types():
                LOG.debug("Registered entity types: {}".format(cls.get_entity_types()))
                raise ValueError("Entity type {} not registered".format(entity_type))

            updating_entity_types.append(entity_type)

        else:
            updating_entity_types.extend(list(cls.entity_type_api_map.keys()))

        db = get_db_handle()

        for entity_type in updating_entity_types:
            query = db.cache_table.delete().where(
                db.cache_table.entity_type == entity_type
            )
            query.execute()

        client = get_api_client()

        for entity_type in updating_entity_types:
            api_suffix = cls.entity_type_api_map[entity_type]
            Obj = get_resource_api(api_suffix, client.connection)
            try:
                res = Obj.get_name_uuid_map({"length": 100})
                for name, uuid in res.items():
                    cls.create(
                        entity_type=entity_type, entity_name=name, entity_uuid=uuid
                    )
            except Exception:
                pc_ip = client.connection.host
                LOG.warning("Cannot fetch data from {}".format(pc_ip))

    @classmethod
    def clear_entities(cls):
        """Deletes all the data present in the cache"""

        db = get_db_handle()
        for db_entity in db.cache_table.select():
            db_entity.delete_instance()

    @classmethod
    def list(cls):
        """return the list of entities stored in db"""

        db = get_db_handle()
        cache_data = []
        for entity in db.cache_table.select():
            cache_data.append(entity.get_detail_dict())

        return cache_data

import peewee
import sys
from collections import OrderedDict
from distutils.version import LooseVersion as LV

from ..db import get_db_handle
from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.tools import get_logging_handle
from calm.dsl.config import get_config

from calm.dsl.api import get_api_client
from calm.dsl.providers import get_provider

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
    def create(cls, entity_type="", entity_name="", entity_uuid=""):
        """Store the uuid of entity in cache"""

        db = get_db_handle()
        db.cache_table.create(
            entity_type=entity_type, entity_name=entity_name, entity_uuid=entity_uuid,
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
    def sync(cls):

        config = get_config()
        client = get_api_client()

        project_name = config["PROJECT"]["name"]
        params = {"length": 1000, "filter": "name=={}".format(project_name)}
        project_name_uuid_map = client.project.get_name_uuid_map(params)

        if not project_name_uuid_map:
            LOG.error("Invalid project {} in config".format(project_name))
            sys.exit(-1)

        project_id = project_name_uuid_map[project_name]
        res, err = client.project.read(project_id)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        project = res.json()
        subnets_list = []
        for subnet in project["status"]["project_status"]["resources"][
            "subnet_reference_list"
        ]:
            subnets_list.append(subnet["uuid"])

        # Extending external subnet's list from remote account
        for subnet in project["status"]["project_status"]["resources"][
            "external_network_list"
        ]:
            subnets_list.append(subnet["uuid"])

        accounts = project["status"]["project_status"]["resources"][
            "account_reference_list"
        ]

        reg_accounts = []
        for account in accounts:
            reg_accounts.append(account["uuid"])

        # Fetching account id from project
        payload = {"filter": "type==nutanix_pc"}
        res, err = client.account.list(payload)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        account_uuid = ""

        for entity in res["entities"]:
            entity_name = entity["metadata"]["name"]
            entity_id = entity["metadata"]["uuid"]
            if entity_id in reg_accounts:
                account_uuid = entity_id
                break

        # Clearing existing data in cache
        cls.clear_entities()

        # Fetch the subnets and images from ahv account registered and store in cache
        Ahv = get_provider("AHV_VM")
        Obj = Ahv.get_api_obj()

        # Fetch ahv images
        payload = {
            "length": 1000,
            "offset": 0,
        }
        ahv_images = {}
        if LV(Obj.get_version()) >= LV("2.9.0"):
            if account_uuid:
                payload["filter"] = "account_uuid=={}".format(account_uuid)
                ahv_images = Obj.images(payload)

        else:
            ahv_images = Obj.images(payload)

        # Store the ahv images
        for entity in ahv_images.get("entities", []):
            cls.create(
                entity_type="AHV_DISK_IMAGE",
                entity_name=entity["status"]["name"],
                entity_uuid=entity["metadata"]["uuid"],
            )

        # Fetch the subnets
        payload = {
            "length": 1000,
            "offset": 0,
            "filter": "(_entity_id_=={})".format(",_entity_id_==".join(subnets_list)),
        }
        ahv_subnets = {}
        if LV(Obj.get_version()) >= LV("2.9.0"):
            if account_uuid:
                payload["filter"] = payload["filter"] + ";account_uuid=={}".format(
                    account_uuid
                )
                ahv_subnets = Obj.subnets(payload)

        else:
            ahv_subnets = Obj.subnets(payload)

        # Store the subnets
        for entity in ahv_subnets.get("entities", []):
            cls.create(
                entity_type="AHV_SUBNET",
                entity_name=entity["status"]["name"],
                entity_uuid=entity["metadata"]["uuid"],
            )

        # Store projects in cache
        project_name_uuid_map = client.project.get_name_uuid_map({"length": 1000})
        for name, uuid in project_name_uuid_map.items():
            cls.create(entity_type="PROJECT", entity_name=name, entity_uuid=uuid)

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

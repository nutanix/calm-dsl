import sys

from .connection import REQUEST
from calm.dsl.config import get_context
from calm.dsl.constants import RESOURCE, MULTICONNECT
from calm.dsl.log import get_logging_handle
from calm.dsl.api.connection import Connection

LOG = get_logging_handle(__name__)


class ResourceAPI:

    ROOT = "api/nutanix/v3"
    CALM_ROOT = "api/calm/v3.0"
    DM_ROOT = "dm/v3"

    def __init__(self, connection, resource_type, calm_api=False, dm_api=False):

        context = get_context()
        ncm_server_config = context.get_ncm_server_config()

        if ncm_server_config.get("ncm_enabled", False):
            # Case when ncm is enabled:
            # If multi connection object is supplied it will return connection object based on resource_type
            # If single connection object is supplied it will return the same connection object
            self.connection = get_resource_type_connection_obj(
                connection, resource_type
            )
        else:
            # Case when ncm is disabled: For all resource type there should be one connection object.
            # If multi connection object is supplied it will return connection.pc_conn_obj
            # If single connection object is supplied it will return the same connection object
            self.connection = get_resource_type_connection_obj(connection)

        if dm_api:
            self.PREFIX = self.DM_ROOT + "/" + resource_type
        else:
            self.PREFIX = (
                (self.CALM_ROOT if calm_api else self.ROOT) + "/" + resource_type
            )

        self.LIST = self.PREFIX + "/list"
        self.ITEM = self.PREFIX + "/{}"

    def create(self, payload):
        return self.connection._call(
            self.PREFIX, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def read(self, id=None):
        url = self.ITEM.format(id) if id else self.PREFIX
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def update(self, uuid, payload):
        return self.connection._call(
            self.ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def delete(self, uuid):
        return self.connection._call(
            self.ITEM.format(uuid), verify=False, method=REQUEST.METHOD.DELETE
        )

    def list(self, params={}, ignore_error=False):
        return self.connection._call(
            self.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
        )

    def get_name_uuid_map(self, params={}):
        res_entities, err = self.list_all(base_params=params, ignore_error=True)

        if not err:
            response = res_entities
        else:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        total_matches = len(response)
        if total_matches == 0:
            return {}
        name_uuid_map = {}

        for entity in response:
            entity_name = entity["status"]["name"]
            entity_uuid = entity["metadata"]["uuid"]

            if entity_name in name_uuid_map:
                uuid = name_uuid_map[entity_name]

                if type(uuid) is str:
                    uuids = uuid.split()
                    uuids.append(entity_uuid)
                    name_uuid_map[entity_name] = uuids

                elif type(uuid) is list:
                    uuid.append(entity_uuid)
                    name_uuid_map[entity_name] = uuid

            else:
                name_uuid_map[entity_name] = entity_uuid

        return name_uuid_map

    def get_uuid_name_map(self, params={}):
        res_entities, err = self.list_all(base_params=params, ignore_error=True)
        if not err:
            response = res_entities
        else:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        total_matches = len(response)
        if total_matches == 0:
            return {}

        uuid_name_map = {}
        for entity in response:
            entity_name = entity["status"]["name"]
            entity_uuid = entity["metadata"]["uuid"]

            uuid_name_map[entity_uuid] = entity_name

        return uuid_name_map

    # TODO: Fix return type of list_all helper
    def list_all(self, api_limit=250, base_params=None, ignore_error=False):
        """returns the list of entities"""

        final_list = []
        offset = 0
        if base_params is None:
            base_params = {}
        params = base_params.copy()
        length = params.get("length", api_limit)
        params["length"] = length
        params["offset"] = offset
        if params.get("sort_attribute", None) is None:
            params["sort_attribute"] = "_created_timestamp_usecs_"
        if params.get("sort_order", None) is None:
            params["sort_order"] = "ASCENDING"
        while True:
            params["offset"] = offset
            response, err = self.list(params, ignore_error=ignore_error)
            if not err:
                response = response.json()
            else:
                if ignore_error:
                    return [], err
                else:
                    raise Exception("[{}] - {}".format(err["code"], err["error"]))

            final_list.extend(response["entities"])

            total_matches = response["metadata"]["total_matches"]
            if int(total_matches) <= (api_limit + offset):
                break

            offset += length

        if ignore_error:
            return final_list, None

        return final_list


def is_ncm_resource(resource_type):
    """
    Returns True if
        -> resource_type matches with existing NCM resources
        -> Else search if existing resource is part of supplied resource_type.
    Usecase:
        1. Let's say "blueprint" is an existing resource type. And API under investigation is of "blueprint" type then return True
        2. Let's say "blueprint" is an existing resource type. And API under investigation is of "blueprint/{some-uuid}".
           Then we check an existing resource "blueprint" is part of "blueprint/{some-uuid}" or not. If yes, "blueprint/{some-uuid}"
           will be routed to host of "blueprint"
    """
    if resource_type in RESOURCE.NCM:
        return True
    if (
        resource_type in RESOURCE.NON_NCM
    ):  # prevent cases when resource_type already exists as NON-NCM resource.
        return False
    return any(existing_resource in resource_type for existing_resource in RESOURCE.NCM)


def is_non_ncm_resource(resource_type):
    """
    Returns True if
        -> resource_type matches with existing NON-NCM resources
        -> Else search if existing resource is part of supplied resource_type.
    Usecase:
        1. Let's say "projects" is an existing resource type. And API under investigation is of "projects" type then return True
        2. Let's say "projects" is an existing resource type. And API under investigation is of "projects/{some-uuid}".
           Then we check an existing resource "projects" is part of "projects/{some-uuid}" or not. If yes, "projects/{some-uuid}"
           will be routed to host of "projects"
    """
    if resource_type in RESOURCE.NON_NCM:
        return True
    if (
        resource_type in RESOURCE.NCM
    ):  # prevent cases when resource_type already exists as NCM resource.
        return False
    return any(
        existing_resource in resource_type for existing_resource in RESOURCE.NON_NCM
    )


def get_resource_type_connection_obj(connection, resource_type=""):
    """
    This routine returns the connection object based on the resource type.
    For single connection object (only one host) it returns same connection object
    For multi connection object (multiple hosts) it returns connection object based on the resource type.

    Returns:
        If resource type is:
            -> NCM, it returns the NCM connection object.
            -> PC, it returns the PC connection object.

    """
    if isinstance(connection, Connection) or resource_type == "groups":
        return connection
    elif is_ncm_resource(resource_type):
        LOG.debug("connection object of {} set to NCM".format(resource_type))
        return getattr(connection, MULTICONNECT.NCM_OBJ)
    elif is_non_ncm_resource(resource_type) or resource_type == "":
        LOG.debug("connection object of {} set to PC".format(resource_type))
        return getattr(connection, MULTICONNECT.PC_OBJ)
    else:
        LOG.error(
            "Invalid resource type '{}', should be one of {}".format(
                resource_type, RESOURCE.NCM | RESOURCE.NON_NCM
            )
        )
        sys.exit("Invalid resource type '{}".format(resource_type))


def get_resource_api(resource_type, connection, calm_api=False, dm_api=False):
    return ResourceAPI(connection, resource_type, calm_api=calm_api, dm_api=dm_api)

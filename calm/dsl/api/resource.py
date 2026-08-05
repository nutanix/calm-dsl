import json

from requests.models import Response
from .connection import REQUEST
from calm.dsl.log import get_logging_handle
from calm.dsl.api.api_connectivity_details_resolver import (
    APIConnectivityDetailsResolver,
)
from calm.dsl.api.ncm_config_util import (
    is_nc_enabled_by_config,
    is_ncm_enabled_by_config,
)


LOG = get_logging_handle(__name__)


class ResourceAPI:

    ROOT = "api/nutanix/v3"

    def __init__(
        self,
        connection,
        resource_type,
        calm_api=False,
        dm_api=False,
        multi_owned=False,
        override_connection=False,
    ):
        api_resolver = APIConnectivityDetailsResolver()
        nc_enabled = is_nc_enabled_by_config()
        ncm_enabled = nc_enabled or is_ncm_enabled_by_config()

        # if override_connection is True, then use the connection passed as argument directly without resolving
        if override_connection:
            self.connection = connection
            api_type = api_resolver._api_owner_resolver.resolve(resource_type)
            self.api_base_path = api_resolver._get_api_path(
                api_type,
                resource_type,
                calm_api or dm_api,
            )
        else:
            connectivity_details = api_resolver.resolve(
                connection,
                resource_type,
                nc_enabled,
                ncm_enabled,
                calm_api or dm_api,
                multi_owned,
            )
            self.connection = connectivity_details.connection
            self.api_base_path = connectivity_details.api_path

        self.list_path = self.api_base_path + "/list"
        self.item_path = self.api_base_path + "/{}"

    def create(self, payload, ignore_error=False):
        return self.connection._call(
            self.api_base_path,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
        )

    def read(self, id=None, ignore_error=False):
        url = self.item_path.format(id) if id else self.api_base_path
        return self.connection._call(
            url, verify=False, method=REQUEST.METHOD.GET, ignore_error=ignore_error
        )

    def update(self, uuid, payload):
        return self.connection._call(
            self.item_path.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def delete(self, uuid):
        return self.connection._call(
            self.item_path.format(uuid), verify=False, method=REQUEST.METHOD.DELETE
        )

    def list(self, params={}, ignore_error=False):
        return self.connection._call(
            self.list_path,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
        )

    def get_name_uuid_map(self, params={}):
        res, err = self.list_all(base_params=params, ignore_error=True)

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entities = res.get("entities", [])
        if not entities:
            return {}
        name_uuid_map = {}

        for entity in entities:
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
        res, err = self.list_all(base_params=params, ignore_error=True)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entities = res.get("entities", [])
        if not entities:
            return {}

        uuid_name_map = {}
        for entity in entities:
            entity_name = entity["status"]["name"]
            entity_uuid = entity["metadata"]["uuid"]

            uuid_name_map[entity_uuid] = entity_name

        return uuid_name_map

    def list_all(self, api_limit=250, base_params=None, ignore_error=False):
        """Returns all entities by paginating through list API.

        Args:
            api_limit (int): Page size for each API call. Defaults to 250.
            base_params (dict): Base query parameters (filter, etc.).
            ignore_error (bool): If True, return error tuple instead of raising.

        Returns:
            tuple: (res, err)
                res (Response): A Response object
                err (dict or None): None if no error occurred, else the error dictionary.
        """
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

        LOG.debug(f"Fetching all entities using list_all routine")

        while True:
            params["offset"] = offset
            response, err = self.list(params, ignore_error=ignore_error)
            if not err:
                response = response.json()
            else:
                if ignore_error:
                    res = Response()
                    return res, err
                else:
                    raise Exception("[{}] - {}".format(err["code"], err["error"]))

            final_list.extend(response["entities"])

            total_matches = response["metadata"]["total_matches"]
            if int(total_matches) <= (api_limit + offset):
                break

            offset += length

        res = Response()
        res.status_code = 200
        res._content = json.dumps({"entities": final_list}).encode("utf-8")
        res.headers["Content-Type"] = "application/json"

        return res, None


def get_resource_api(
    resource_type,
    connection,
    calm_api=False,
    dm_api=False,
    multi_owned=False,
    override_connection=False,
):
    return ResourceAPI(
        connection,
        resource_type,
        calm_api=calm_api,
        dm_api=dm_api,
        multi_owned=multi_owned,
        override_connection=override_connection,
    )

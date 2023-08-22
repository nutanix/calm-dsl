import sys
import time
import json

import arrow
import click

from calm.dsl.api import get_api_client
from .providers import get_custom_provider

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_resource_types(account_uuid):
    """returns resource_types POST call data"""

    client = get_api_client()
    res, err = client.account.resource_types_list(account_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def update_resource_types(
    resource_type_payload, account_uuid, name=None, updated_name=None
):

    client = get_api_client()

    resource_type_payload.pop("status", None)

    # updating the name of the resource_type to updated_name if provided otherwise it is kept as it is originally
    resource_type_payload["spec"]["name"] = updated_name or name
    resource_type_payload["metadata"]["name"] = updated_name or name

    resource_type_resources = resource_type_payload["spec"]["resources"]
    resource_type_name = resource_type_payload["spec"]["name"]

    resource_types = get_resource_types(account_uuid)
    resource_type = resource_types.get("entities", [])[0]
    uuid = resource_type["metadata"]["uuid"]
    spec_version = resource_type["metadata"]["spec_version"]

    provider = get_custom_provider(updated_name or name)

    resource_type_resources["provider_reference"]["uuid"] = provider["metadata"]["uuid"]

    # creting updated resource_type payload
    resource_type_payload = {
        "spec": {"name": resource_type_name, "resources": resource_type_resources},
        "metadata": {
            "use_categories_mapping": False,
            "spec_version": spec_version,
            "name": resource_type_name,
            "kind": "resource_type",
        },
        "api_version": "3.0",
    }

    return client.resource_types.update(uuid, resource_type_payload)


def create_resource_type(resource_type_payload, name):
    """
    creates resource_type

    Args:
        resource_type_payload(dict): payload for resource_type creation
    """

    client = get_api_client()

    if name:
        resource_type_payload["spec"]["name"] = name

    LOG.info("Creating resource type")

    res, err = client.resource_types.create(resource_type_payload)

    if err:
        LOG.error(err)
        sys.exit(-1)

    LOG.info("Resource Type Created")
    LOG.info(res.json())

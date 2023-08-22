import sys
import time
import json

import arrow
import click

from calm.dsl.api import get_api_client

from .utils import (
    highlight_text,
)

from calm.dsl.builtins.models.helper.common import get_provider_uuid
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_custom_provider(name, provider_uuid=None):
    """returns provider get call data"""

    client = get_api_client()
    if not provider_uuid:
        provider_uuid = get_provider_uuid(name=name)
    res, err = client.provider.read(provider_uuid)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def update_custom_provider(provider_payload, name=None, updated_name=None):
    """Updates a provider"""

    client = get_api_client()
    provider_payload.pop("status", None)

    provider_payload["spec"]["name"] = updated_name or name
    provider_payload["metadata"]["name"] = (
        updated_name or provider_payload["spec"]["name"]
    )

    provider_resources = provider_payload["spec"]["resources"]
    provider_name = provider_payload["spec"]["name"]

    provider = get_custom_provider(name=name)
    uuid = provider["metadata"]["uuid"]
    spec_version = provider["metadata"]["spec_version"]

    provider_payload = {
        "spec": {"name": provider_name, "resources": provider_resources},
        "metadata": {
            "use_categories_mapping": False,
            "spec_version": spec_version,
            "name": provider_name,
            "kind": "provider",
        },
        "api_version": "3.0",
    }

    return client.provider.update(uuid, provider_payload)


def create_custom_provider(provider_payload, name):
    """
    creates provider

    Args:
        provider_payload(dict): payload for provider creation
    """

    client = get_api_client()

    if name:
        provider_payload["spec"]["name"] = name

    LOG.info("Creting provider")

    res, err = client.provider.create(provider_payload)

    if err:
        LOG.error(err)
        sys.exit(-1)

    LOG.info("Provider Created")


def describe_custom_provider(provider_name, out):
    """Displays provider data"""

    provider = get_custom_provider(provider_name)

    if out == "json":
        provider.pop("status", None)
        click.echo(json.dumps(provider, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Provider Summary----\n")

    click.echo(
        "Name: "
        + highlight_text(provider_name)
        + " (uuid: "
        + highlight_text(provider["metadata"]["uuid"])
        + ")"
    )
    click.echo("Status: " + highlight_text(provider["status"]["state"]))
    click.echo(
        "Owner: " + highlight_text(provider["metadata"]["owner_reference"]["name"])
    )
    created_on = int(provider["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    provider_resources = provider.get("status").get("resources", {})
    click.echo("Infra Type: " + highlight_text(provider_resources["infra_type"]))
    click.echo("Provider Type: " + highlight_text(provider_resources["type"] + "\n"))

    auth_schema_list = provider["spec"]["resources"]["auth_schema_list"]

    click.echo("Variables")
    for schema_variable in auth_schema_list:
        if (provider_name == "NDB") and (schema_variable["name"] == "ndb__insecure"):
            continue
        click.echo(
            "\t{}".format(
                highlight_text(
                    "{} ({}, {}, {})".format(
                        schema_variable["label"],
                        schema_variable["val_type"],
                        schema_variable["type"],
                        (
                            "Mandatory"
                            if schema_variable["is_mandatory"]
                            else "Not Mandatory"
                        ),
                    )
                )
            )
        )

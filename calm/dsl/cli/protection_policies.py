import click
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.log import get_logging_handle
from .utils import highlight_text

LOG = get_logging_handle(__name__)


def get_protection_policies(limit, offset, quiet):
    """
    Returns protection policies along with the protection rules in the project
    """

    client = get_api_client()
    LOG.info("Fetching protection policies")
    params = {"length": limit, "offset": offset}
    res, err = client.app_protection_policy.list(params)
    if err:
        LOG.error(err)
        sys.exit("Unable to list protection policies")
    res = res.json()["entities"]
    if not res:
        click.echo(highlight_text("No protection policy found !!!\n"))
        return

    table = PrettyTable()

    if quiet:
        table.field_names = ["NAME", "RULE NAME"]
        for entity in res:
            name = entity["status"]["name"]
            for rule in entity["status"]["resources"]["app_protection_rule_list"]:
                rule_name = rule["name"]
                table.add_row([highlight_text(name), highlight_text(rule_name)])
        click.echo(table)
        return

    table.field_names = [
        "NAME",
        "UUID",
        "RULE NAME",
        "RULE UUID",
    ]

    for entity in res:
        name = entity["status"]["name"]
        uuid = entity["metadata"]["uuid"]
        for rule in entity["status"]["resources"]["app_protection_rule_list"]:
            rule_name = rule["name"]
            rule_uuid = rule["uuid"]
            table.add_row(
                [
                    highlight_text(name),
                    highlight_text(uuid),
                    highlight_text(rule_name),
                    highlight_text(rule_uuid),
                ]
            )

    click.echo(table)

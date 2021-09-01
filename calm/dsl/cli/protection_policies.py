import click
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client, get_resource_api
from calm.dsl.builtins.models.helper.common import get_project
from calm.dsl.log import get_logging_handle
from .utils import highlight_text

LOG = get_logging_handle(__name__)


def get_protection_policies(limit, offset, project_name, quiet):
    """
    Returns protection policies along with the protection rules in the project
    """

    client = get_api_client()
    LOG.info("Fetching protection policies")
    params = {"length": limit, "offset": offset}
    if project_name:
        project = get_project(project_name)
        params["filter"] = "project_reference=={}".format(project["metadata"]["uuid"])
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
        "RULE TYPE",
        "EXPIRY (DAYS)",
        "PROJECT",
    ]

    for entity in res:
        name = entity["status"]["name"]
        uuid = entity["metadata"]["uuid"]
        project_reference = entity["metadata"].get("project_reference", {})
        for rule in entity["status"]["resources"]["app_protection_rule_list"]:
            expiry = 0
            rule_type = ""
            if rule.get("remote_snapshot_retention_policy", {}):
                rule_type = "Remote"
                expiry = (
                    rule["remote_snapshot_retention_policy"]
                    .get("snapshot_expiry_policy", {})
                    .get("multiple", "")
                )
            elif rule.get("local_snapshot_retention_policy", {}):
                rule_type = "Local"
                expiry = (
                    rule["local_snapshot_retention_policy"]
                    .get("snapshot_expiry_policy", {})
                    .get("multiple", "")
                )
            rule_name = rule["name"]
            rule_uuid = rule["uuid"]
            if not expiry:
                expiry = "-"
            table.add_row(
                [
                    highlight_text(name),
                    highlight_text(uuid),
                    highlight_text(rule_name),
                    highlight_text(rule_uuid),
                    highlight_text(rule_type),
                    highlight_text(expiry),
                    highlight_text(project_reference.get("name", "")),
                ]
            )

    click.echo(table)

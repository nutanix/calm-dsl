import time
import sys
import json
import arrow
import click
from prettytable import PrettyTable

from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .utils import (
    highlight_text,
    get_name_query,
)
from .constants import APPROVAL_REQUEST

LOG = get_logging_handle(__name__)


def describe_approval(approval_name, out, uuid=""):
    """Displays approval data"""

    client = get_api_client()
    approval = get_approval(client, approval_name, uuid=uuid)

    if out == "json":
        approval.pop("status", None)
        click.echo(
            json.dumps(approval, indent=4, separators=(",", ": "), ensure_ascii=False)
        )
        return

    click.echo("\n----Approval Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(approval["status"]["name"])
        + " (uuid: "
        + highlight_text(approval["metadata"]["uuid"])
        + ")"
    )
    click.echo("Status: " + highlight_text(approval["status"]["resources"]["state"]))
    click.echo(
        "Project: "
        + highlight_text(approval["status"]["resources"]["project_reference"]["name"])
    )
    click.echo(
        "Policy: "
        + highlight_text(approval["status"]["resources"]["policy_reference"]["name"])
    )
    created_on = int(approval["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Initiated: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    expires = int(approval["metadata"]["expiry_time"]) // 1000000
    past = arrow.get(expires).humanize()
    click.echo(
        "Expires: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    click.echo(
        "Requested By: "
        + highlight_text(approval["status"]["resources"]["owner_reference"]["name"]),
        nl=False,
    )

    condition_list = (
        approval.get("status").get("resources", {}).get("condition_list", [])
    )
    click.echo("\nConditions [{}]:".format(highlight_text(len(condition_list))))
    for condition in condition_list:
        attribute_name = condition.get("attribute_name")
        for criteria in condition.get("criteria_list", []):
            if not criteria["is_primary"]:
                continue
            operator = criteria["operator"]
            rhs = criteria["rhs"]
            click.echo(
                "\tCriteria Description: {}".format(
                    highlight_text(attribute_name)
                    + " "
                    + highlight_text(operator)
                    + " "
                    + highlight_text(rhs)
                )
            )

    approval_set_list = (
        approval.get("status").get("resources", {}).get("approval_set_list", [])
    )
    click.echo("Approver Sets [{}]:".format(highlight_text(len(approval_set_list))))
    for approval_set in approval_set_list:
        approver_set_name = approval_set.get("name", "")
        approver_set_type = approval_set.get("type", "")
        approver_set_state = approval_set.get("state", "")
        is_current_approver_set = approval_set.get("is_current", "")
        if is_current_approver_set:
            click.echo(
                "\tApprover Set: {}".format(
                    highlight_text(approver_set_name)
                    + " "
                    + highlight_text("(Current)")
                )
            )
        else:
            click.echo("\tApprover Set: {}".format(highlight_text(approver_set_name)))
        click.echo("\tApprover Set Type: {}".format(highlight_text(approver_set_type)))
        click.echo(
            "\tApprover Set State: {}".format(highlight_text(approver_set_state))
        )

        approval_element_list = approval_set.get("approval_element_list", [])
        click.echo(
            "\tApprovers [{}]:".format(highlight_text(len(approval_element_list)))
        )
        for approval_element in approval_element_list:

            approver_state = approval_element.get("state", "")
            approver_name = approval_element.get("approver_reference", {}).get(
                "name", ""
            )
            approver_comment = approval_element.get("comment", "")
            is_current_approver = approval_element.get("is_current", "")
            if is_current_approver:
                click.echo(
                    "\t\tApprover: {}".format(
                        highlight_text(approver_name) + " " + highlight_text("(You)")
                    )
                )
            else:
                click.echo("\t\tApprover: {}".format(highlight_text(approver_name)))

            click.echo("\t\tApprover State: {}".format(highlight_text(approver_state)))
            if approver_comment:
                click.echo(
                    "\t\tApprover Comment: {}".format(highlight_text(approver_comment))
                )


def update_approval(client, name, state, comment="", uuid=""):

    approval = get_approval(client, name, uuid)
    approval_uuid = approval["metadata"]["uuid"]

    if approval["status"]["resources"]["state"] in APPROVAL_REQUEST.TERMINAL_STATES:
        err_msg = "Approval is already {}".format(
            approval["status"]["resources"]["state"]
        )
        err = {"error": err_msg, "code": -1}
        return None, err

    set_uuid = ""
    element_uuid = ""
    for approver_set in approval["status"]["resources"]["approval_set_list"]:
        if approver_set["is_current"]:
            set_uuid = approver_set["uuid"]
            for approver_element in approver_set["approval_element_list"]:
                if approver_element["is_current"]:
                    element_uuid = approver_element["uuid"]
                    break
            break
    if not (set_uuid and element_uuid):
        err_msg = "Current user cannot act on approvals"
        err = {"error": err_msg, "code": -1}
        return None, err

    spec_version = approval["status"]["resources"]["spec_version"]
    return client.approvals.update_approval(
        approval_uuid, set_uuid, element_uuid, state, spec_version, comment
    )


def update_approval_command(name, state, comment="", uuid=""):
    """Updates a approval"""

    client = get_api_client()

    res, err = update_approval(client, name, state, comment, uuid)
    if err:
        LOG.error(err["error"])
        return

    approval = res.json()
    approval_name = approval["metadata"]["name"]
    approval_res = approval.get("status", {}).get("resources", {})
    approval_state = approval_res.get("state", "DRAFT")

    # in case of single request from approval we need to fetch uuid explicitly from metadata
    if not uuid:
        approval = get_approval(client, name, uuid)
        approval_uuid = approval["metadata"]["uuid"]
    else:
        approval_uuid = uuid

    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/policies/approvals/requests/{}".format(
        pc_ip, pc_port, approval_uuid
    )
    stdout_dict = {"name": approval_name, "link": link, "state": approval_state}
    click.echo(
        json.dumps(stdout_dict, indent=4, separators=(",", ": "), ensure_ascii=False)
    )


def get_approval(client, approval_name, uuid=""):

    if uuid:
        params = {"filter": "name=={};uuid=={}".format(approval_name, uuid)}
    else:
        params = {"filter": "name=={}".format(approval_name)}

    res, err = client.approvals.list(params=params)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Approval list call with params {} failed with error {}".format(
                params, err["error"]
            )
        )
        sys.exit("Approval list call failed")

    response = res.json()
    entities = response.get("entities", None)
    approval = None
    if entities:
        if len(entities) != 1:
            LOG.error("More than one approvals found, please specify UUID")
            sys.exit("More than one approvals found, please specify UUID")

        LOG.info("{} found ".format(approval_name))
        approval = entities[0]
    else:
        LOG.error("Approval with name {} not found".format(approval_name))
        sys.exit("Approval with name={} not found".format(approval_name))

    approval_uuid = approval["metadata"]["uuid"]
    LOG.info("Fetching approval details")
    res, err = client.approvals.read(approval_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error("Approval get on uuid {} failed".format(approval_uuid))
        sys.exit("Approval get on uuid={} failed".format(approval_uuid))

    approval = res.json()
    return approval


def get_approval_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the approvals, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if not all_items:
        filter_query += ";pending_on_me==true"
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.approvals.list(params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch policies from {}".format(pc_ip))
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    total_matches = int(total_matches)
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(
            json.dumps(res, indent=4, separators=(",", ": "), ensure_ascii=False)
        )
        return

    json_rows = res["entities"]
    if not json_rows:
        click.echo(highlight_text("No approval found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "REQUEST",
        "STATE",
        "REQUESTED BY",
        "INITIATED",
        "EXPIRES",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        initiated = int(metadata["creation_time"]) // 1000000
        expires = int(metadata["expiry_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["resources"]["state"]),
                highlight_text(row["resources"]["owner_reference"].get("name", "")),
                "{}".format(arrow.get(initiated).humanize()),
                "{}".format(arrow.get(expires).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)

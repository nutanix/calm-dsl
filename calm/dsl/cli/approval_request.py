import time
import sys
import json
import arrow
import click
from prettytable import PrettyTable

from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .utils import highlight_text, get_name_query, get_states_filter
from .constants import APPROVAL_REQUEST

LOG = get_logging_handle(__name__)


def describe_approval_request(approval_request_name, out, uuid=""):
    """Displays approval request data"""

    client = get_api_client()
    approval_request = get_approval_request(client, approval_request_name, uuid=uuid)

    if out == "json":
        approval_request.pop("status", None)
        click.echo(
            json.dumps(
                approval_request, indent=4, separators=(",", ": "), ensure_ascii=False
            )
        )
        return

    click.echo("\n----Approval request Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(approval_request["status"]["name"])
        + " (uuid: "
        + highlight_text(approval_request["metadata"]["uuid"])
        + ")"
    )
    click.echo(
        "Status: " + highlight_text(approval_request["status"]["resources"]["state"])
    )
    click.echo(
        "Project: "
        + highlight_text(
            approval_request["status"]["resources"]["project_reference"]["name"]
        )
    )
    click.echo(
        "Policy: "
        + highlight_text(
            approval_request["status"]["resources"]["policy_reference"]["name"]
        )
    )
    created_on = int(approval_request["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Initiated: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    expires = int(approval_request["metadata"]["expiry_time"]) // 1000000
    past = arrow.get(expires).humanize()
    click.echo(
        "Expires: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    click.echo(
        "Requested By: "
        + highlight_text(
            approval_request["status"]["resources"]["owner_reference"]["name"]
        ),
        nl=False,
    )

    condition_list = (
        approval_request.get("status").get("resources", {}).get("condition_list", [])
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

    approval_request_set_list = (
        approval_request.get("status").get("resources", {}).get("approval_set_list", [])
    )
    click.echo(
        "Approver Sets [{}]:".format(highlight_text(len(approval_request_set_list)))
    )
    for approval_request_set in approval_request_set_list:
        approver_set_name = approval_request_set.get("name", "")
        approver_set_type = approval_request_set.get("type", "")
        approver_set_state = approval_request_set.get("state", "")
        is_current_approver_set = approval_request_set.get("is_current", "")
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

        approval_request_element_list = approval_request_set.get(
            "approval_element_list", []
        )
        click.echo(
            "\tApprovers [{}]:".format(
                highlight_text(len(approval_request_element_list))
            )
        )
        for approval_request_element in approval_request_element_list:

            approver_state = approval_request_element.get("state", "")
            approver_name = approval_request_element.get("approver_reference", {}).get(
                "name", ""
            )
            approver_comment = approval_request_element.get("comment", "")
            is_current_approver = approval_request_element.get("is_current", "")
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


def get_approval_request(client, approval_request_name, uuid=""):

    if uuid:
        params = {"filter": "name=={};uuid=={}".format(approval_request_name, uuid)}
    else:
        params = {"filter": "name=={}".format(approval_request_name)}
    res, err = client.approval_requests.list(params=params)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Approval request request list call with params {} failed with error {}".format(
                params, err["error"]
            )
        )
        sys.exit("Approval request request list call failed")

    response = res.json()
    entities = response.get("entities", None)
    approval_request = None
    if entities:
        if len(entities) != 1:
            sys.exit("More than one approval request found, please specify UUID")

        LOG.info("{} found ".format(approval_request_name))
        approval_request = entities[0]
    else:
        LOG.error(
            "Approval request request with name {} not found".format(
                approval_request_name
            )
        )
        sys.exit(
            "Approval request request with name={} not found".format(
                approval_request_name
            )
        )

    approval_request_id = approval_request["metadata"]["uuid"]
    LOG.info("Fetching approval_request request details")
    res, err = client.approval_requests.read(approval_request_id)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Approval request request get on uuid {} failed".format(approval_request_id)
        )
        sys.exit(
            "Approval request request get on uuid={} failed".format(approval_request_id)
        )

    approval_request = res.json()
    return approval_request


def get_approval_request_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the approval requests, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if all_items:
        filter_query += get_states_filter(APPROVAL_REQUEST.STATES)
    else:
        filter_query += get_states_filter(
            APPROVAL_REQUEST.STATES, states=[APPROVAL_REQUEST.STATES.PENDING]
        )
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.approval_requests.list(params=params)

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
        click.echo(highlight_text("No approval request found !!!\n"))
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
                "{}".format(arrow.get(initiated).humanize()),
                "{}".format(arrow.get(expires).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)

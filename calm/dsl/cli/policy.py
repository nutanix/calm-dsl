import time
import sys
import json
import arrow
import click
from ruamel import yaml
from prettytable import PrettyTable

from calm.dsl.builtins import Ref
from calm.dsl.builtins.models.policy import Policy
from calm.dsl.builtins.models.policy_payload import create_policy_payload
from calm.dsl.builtins.models.helper.common import get_cur_context_project
from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .utils import highlight_text, get_name_query, get_states_filter
from calm.dsl.constants import CACHE, POLICY
from calm.dsl.store import Cache
from calm.dsl.tools import get_module_from_file
from .constants import POLICY as CLI_POLICY, APPROVAL_REQUEST

LOG = get_logging_handle(__name__)


def describe_policy(policy_name, out):
    """Displays policy data"""

    client = get_api_client()
    policy = get_policy(client, policy_name)

    if out == "json":
        policy.pop("status", None)
        click.echo(
            json.dumps(policy, indent=4, separators=(",", ": "), ensure_ascii=False)
        )
        return

    click.echo("\n----Policy Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(policy_name)
        + " (uuid: "
        + highlight_text(policy["metadata"]["uuid"])
        + ")"
    )
    click.echo("Description: " + highlight_text(policy["status"]["description"]))

    policy_scope = (
        policy["spec"]["resources"].get("category_list", {}).get("Project", "-")
    )
    click.echo("Scope: " + highlight_text(policy_scope))

    click.echo("Status: " + highlight_text(policy["status"]["resources"]["state"]))
    click.echo(
        "Owner: "
        + highlight_text(policy["metadata"].get("owner_reference", {}).get("name", "-"))
    )

    created_on = int(policy["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Created: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    policy_resources = policy.get("status").get("resources", {})
    event = policy_resources.get("event_reference", {})
    if event:
        event_data = Cache.get_entity_data_using_uuid(
            entity_type=CACHE.ENTITY.POLICY_EVENT, uuid=event["uuid"]
        )
        event_name = event_data["entity_type"] + "_" + event_data["name"]
        click.echo("Event: {}".format(highlight_text(event_name)))
    criteria_list = policy.get("status").get("resources", {}).get("criteria_list", [])
    click.echo("Criterias [{}]:".format(highlight_text(len(criteria_list))))
    for criteria in criteria_list:
        lhs = criteria["lhs"]
        operator = criteria["operator"]
        rhs = criteria["rhs"]
        click.echo(
            "\tCriteria Description: {}".format(
                highlight_text(lhs)
                + " "
                + highlight_text(operator)
                + " "
                + highlight_text(rhs)
            )
        )

    action_list = policy.get("status").get("resources", {}).get("action_list", [])
    click.echo("Actions [{}]:".format(highlight_text(len(action_list))))
    for action in action_list:
        action_type = action["action_type_reference"]["name"]
        click.echo("\tAction Type: {}".format(highlight_text(action_type)))
        if action_type == POLICY.ACTION_TYPE.APPROVAL:
            approver_set_list = action.get("attrs", {}).get("approver_set_list", [])
            click.echo(
                "\tApprover Sets [{}]:".format(highlight_text(len(approver_set_list)))
            )
            for approver_set in approver_set_list:
                approver_set_name = approver_set.get("name", "")
                approver_set_type = approver_set.get("type", "")
                click.echo(
                    "\n\t\tApprover Set Name: {}".format(
                        highlight_text(approver_set_name)
                    )
                )
                click.echo(
                    "\t\tApprover Set Type: {}".format(
                        highlight_text(approver_set_type)
                    )
                )

                user_list = approver_set.get("user_reference_list", [])
                click.echo("\t\tUsers [{}]:".format(highlight_text(len(user_list))))
                for user in user_list:
                    user_name = user.get("name", "")
                    click.echo("\t\t\t" + highlight_text(user_name))

                user_group_list = approver_set.get("user_group_reference_list", [])
                click.echo(
                    "\t\tUser Groups [{}]:".format(highlight_text(len(user_group_list)))
                )
                for group in user_group_list:
                    group_name = group.get("name", "")
                    click.echo("\t\t\t" + highlight_text(group_name))

                external_user_list = approver_set.get("external_user_list", [])
                click.echo(
                    "\t\tExternal Users [{}]:".format(
                        highlight_text(len(external_user_list))
                    )
                )
                for user in external_user_list:
                    user_email = user.get("email", "")
                    click.echo("\t\t\t" + highlight_text(user_email))


def get_policy_module_from_file(policy_file):
    """Return Policy module given a user policy dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_policy", policy_file)


def get_policy_class_from_module(policy_module):
    """Returns policy class given a module"""

    UserPolicy = None
    for item in dir(policy_module):
        obj = getattr(policy_module, item)
        if isinstance(obj, type(Policy)):
            UserPolicy = obj
    return UserPolicy


def compile_policy(policy_file):

    # Constructing metadata payload
    # Note: This should be constructed before loading policy module. As metadata will be used while getting policy_payload
    metadata_payload = get_metadata_payload(policy_file)
    user_policy_module = get_policy_module_from_file(policy_file)
    UserPolicy = get_policy_class_from_module(user_policy_module)
    if UserPolicy is None:
        return None

    UserPolicyPayload, _ = create_policy_payload(UserPolicy, metadata=metadata_payload)
    policy_payload = UserPolicyPayload.get_dict()

    return policy_payload


def compile_policy_command(policy_file, out):

    policy_payload = compile_policy(policy_file)
    if policy_payload is None:
        LOG.error("User policy not found in {}".format(policy_payload))
        return

    if out == "json":
        click.echo(
            json.dumps(
                policy_payload, indent=4, separators=(",", ": "), ensure_ascii=False
            )
        )
    elif out == "yaml":
        click.echo(yaml.dump(policy_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_policy(
    client, policy_payload, name=None, description=None, force_create=False
):

    policy_payload.pop("status", None)

    if name:
        policy_payload["spec"]["name"] = name
        policy_payload["metadata"]["name"] = name

    if description:
        policy_payload["spec"]["description"] = description

    # add project ref
    project_cache_data = get_cur_context_project()
    project_name = project_cache_data["name"]
    policy_payload["metadata"]["project_reference"] = Ref.Project(project_name)

    # add category list
    if "Project" not in policy_payload["spec"]["resources"]["category_list"]:
        policy_payload["spec"]["resources"]["category_list"]["Project"] = project_name
    client = get_api_client()
    return client.policy.create(policy_payload)


def update_policy(client, policy_payload, name=None, description=None):

    policy_payload.pop("status", None)

    if name:
        policy_payload["spec"]["name"] = name
        policy_payload["metadata"]["name"] = name

    if description:
        policy_payload["spec"]["description"] = description

    policy = get_policy(client, policy_payload["spec"]["name"])
    policy_payload["metadata"]["spec_version"] = policy["metadata"]["spec_version"]
    uuid = policy["metadata"]["uuid"]

    policy_old_project_name = (
        policy["metadata"].get("project_reference", {}).get("name", "")
    )
    policy_new_project_name = (
        policy_payload["metadata"].get("project_reference", {}).get("name", "")
    )
    if policy_new_project_name != policy_old_project_name:
        LOG.warning(
            "Project (Policy Scope) will be changed to {} from {}".format(
                policy_new_project_name, policy_old_project_name
            )
        )

    return client.policy.update(uuid, policy_payload)


def update_policy_from_json(client, path_to_json, name=None, description=None):

    policy_payload = json.loads(open(path_to_json, "r").read())
    return update_policy(client, policy_payload, name=name, description=description)


def update_policy_from_dsl(client, policy_file, name=None, description=None):

    policy_payload = compile_policy(policy_file)
    if policy_payload is None:
        err_msg = "Policy not found in {}".format(policy_file)
        err = {"error": err_msg, "code": -1}
        return None, err

    return update_policy(client, policy_payload, name=name, description=description)


def enable_policy_command(name):
    """Updates a policy"""

    client = get_api_client()
    policy_payload = get_policy(client, name)
    policy_payload["spec"]["resources"]["enabled"] = True
    res, err = update_policy(client, policy_payload)
    if err:
        LOG.error(err["error"])
        return

    policy = res.json()
    policy_uuid = policy["metadata"]["uuid"]
    policy_name = policy["metadata"]["name"]
    policy_res = policy.get("status", {}).get("resources", {})
    policy_state = policy_res.get("state", "DRAFT")
    LOG.debug("Policy {} has state: {}".format(policy_name, policy_state))

    if policy_state == "DRAFT":
        msg_list = policy_res.get("message_list", [])
        if not msg_list:
            LOG.error("Policy {} updated with errors.".format(policy_name))
            LOG.debug(json.dumps(policy_res))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Policy {} updated with {} error(s): {}".format(
                policy_name, len(msg_list), msgs
            )
        )
        sys.exit(-1)

    LOG.info("Policy {} enabled successfully.".format(policy_name))
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/policies/approvals/{}".format(
        pc_ip, pc_port, policy_uuid
    )
    stdout_dict = {"name": policy_name, "link": link, "state": policy_state}
    click.echo(
        json.dumps(stdout_dict, indent=4, separators=(",", ": "), ensure_ascii=False)
    )


def disable_policy_command(name):
    """Updates a policy"""

    client = get_api_client()
    policy_payload = get_policy(client, name)
    policy_payload["spec"]["resources"]["enabled"] = False
    res, err = update_policy(client, policy_payload)
    if err:
        LOG.error(err["error"])
        return

    policy = res.json()
    policy_uuid = policy["metadata"]["uuid"]
    policy_name = policy["metadata"]["name"]
    policy_res = policy.get("status", {}).get("resources", {})
    policy_state = policy_res.get("state", "DRAFT")
    LOG.debug("Policy {} has state: {}".format(policy_name, policy_state))

    if policy_state == "DRAFT":
        msg_list = policy_res.get("message_list", [])
        if not msg_list:
            LOG.error("Policy {} updated with errors.".format(policy_name))
            LOG.debug(json.dumps(policy_res))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Policy {} updated with {} error(s): {}".format(
                policy_name, len(msg_list), msgs
            )
        )
        sys.exit(-1)

    LOG.info("Policy {} disabled successfully.".format(policy_name))
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/policies/approvals/{}".format(
        pc_ip, pc_port, policy_uuid
    )
    stdout_dict = {"name": policy_name, "link": link, "state": policy_state}
    click.echo(
        json.dumps(stdout_dict, indent=4, separators=(",", ": "), ensure_ascii=False)
    )


def update_policy_command(policy_file, name, description):
    """Updates a policy"""

    client = get_api_client()

    if policy_file.endswith(".json"):
        res, err = update_policy_from_json(
            client, policy_file, name=name, description=description
        )
    elif policy_file.endswith(".py"):
        res, err = update_policy_from_dsl(
            client, policy_file, name=name, description=description
        )
    else:
        LOG.error("Unknown file format {}".format(policy_file))
        return

    if err:
        LOG.error(err["error"])
        return

    policy = res.json()
    policy_uuid = policy["metadata"]["uuid"]
    policy_name = policy["metadata"]["name"]
    policy_res = policy.get("status", {}).get("resources", {})
    policy_state = policy_res.get("state", "DRAFT")
    LOG.debug("Runbook {} has state: {}".format(policy_name, policy_state))

    if policy_state == "DRAFT":
        msg_list = policy_res.get("message_list", [])
        if not msg_list:
            LOG.error("Policy {} updated with errors.".format(policy_name))
            LOG.debug(json.dumps(policy_res))
            sys.exit(-1)

        msgs = []
        for msg_dict in msg_list:
            msgs.append(msg_dict.get("message", ""))

        LOG.error(
            "Policy {} updated with {} error(s): {}".format(
                policy_name, len(msg_list), msgs
            )
        )
        sys.exit(-1)

    LOG.info("Policy {} updated successfully.".format(policy_name))
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/policies/approvals/{}".format(
        pc_ip, pc_port, policy_uuid
    )
    stdout_dict = {"name": policy_name, "link": link, "state": policy_state}
    click.echo(
        json.dumps(stdout_dict, indent=4, separators=(",", ": "), ensure_ascii=False)
    )


def get_policy(client, policy_name):

    params = {"filter": "name=={}".format(policy_name)}
    res, err = client.policy.list(params=params)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Policy list call with params {} failed with error {}".format(
                params, err["error"]
            )
        )
        sys.exit("Policy list call failed")

    response = res.json()
    entities = response.get("entities", None)
    policy = None
    if entities:
        if len(entities) != 1:
            LOG.error("More than one policy found - {}".format(entities))
            sys.exit("More than one policy found")

        LOG.info("{} found ".format(policy_name))
        policy = entities[0]
    else:
        LOG.error("Policy with name {} not found".format(policy_name))
        sys.exit("Policy with name={} not found".format(policy_name))

    policy_id = policy["metadata"]["uuid"]
    LOG.info("Fetching policy details")
    res, err = client.policy.read(policy_id)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error("Policy get on uuid {} failed".format(policy_id))
        sys.exit("Policy get on uuid={} failed".format(policy_id))

    policy = res.json()
    return policy


def get_policy_execution(client, policy_name, uuid=""):

    policy = get_policy(client, policy_name)
    policy_uuid = policy["metadata"]["uuid"]

    if uuid:
        params = {"filter": "uuid=={}".format(uuid)}
    else:
        params = {}

    res, err = client.policy.list_policy_execution(uuid=policy_uuid, params=params)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Policy execution list call with params {} failed with error {}".format(
                params, err["error"]
            )
        )
        sys.exit("Policy execution list call failed")

    response = res.json()
    entities = response.get("entities", None)
    if entities:
        if len(entities) != 1:
            sys.exit("More than one policy execution found, please specify UUID")

        policy_exec = entities[0]
    else:
        LOG.error("Policy execution for policy {} not found".format(policy_name))
        sys.exit("Policy execution for policy {} not found".format(policy_name))

    exec_uuid = policy_exec["metadata"]["uuid"]
    LOG.info("Fetching policy execution details")
    res, err = client.policy.get_policy_execution(policy_uuid, exec_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error("Policy get on uuid {} failed".format(exec_uuid))
        sys.exit("Policy get on uuid={} failed".format(exec_uuid))

    policy_exec = res.json()
    return policy_exec


def get_policy_list(name, filter_by, limit, offset, quiet, all_items, out):
    """Get the policies, optionally filtered by a string"""

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    filter_query = ""
    if name:
        filter_query = get_name_query([name])
    if filter_by:
        filter_query = filter_query + ";(" + filter_by + ")"
    if all_items:
        filter_query += get_states_filter(CLI_POLICY.STATES)
    if filter_query.startswith(";"):
        filter_query = filter_query[1:]

    if filter_query:
        params["filter"] = filter_query

    res, err = client.policy.list(params=params)

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
        click.echo(highlight_text("No policy found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "STATE",
        "SCOPE",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        created_on = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000
        scope = metadata.get("project_reference", {}).get("name", "")

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["resources"]["state"]),
                highlight_text(scope),
                "{}".format(arrow.get(created_on).humanize()),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def delete_policy(policy_names):
    client = get_api_client()
    for policy_name in policy_names:
        policy = get_policy(client, policy_name)
        policy_id = policy["metadata"]["uuid"]
        _, err = client.policy.delete(policy_id)
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            LOG.error("Delete on policy with uuid {} failed".format(policy_id))
            sys.exit("Delete on policy with uuid={} failed".format(policy_id))
        LOG.info("Policy {} deleted".format(policy_name))

    LOG.info("[Done]")


def create_policy_from_json(
    client, path_to_json, name=None, description=None, force_create=False
):

    policy_payload = json.loads(open(path_to_json, "r").read())
    return create_policy(
        client,
        policy_payload,
        name=name,
        description=description,
        force_create=force_create,
    )


def create_policy_from_dsl(
    client, policy_file, name=None, description=None, force_create=False
):

    policy_payload = compile_policy(policy_file)
    if policy_payload is None:
        err_msg = "User policy not found in {}".format(policy_file)
        err = {"error": err_msg, "code": -1}
        return None, err
    return create_policy(
        client,
        policy_payload,
        name=name,
        description=description,
        force_create=force_create,
    )


def create_policy_command(policy_file, name, description, force):
    """Creates a policy"""

    client = get_api_client()
    if policy_file.endswith(".json"):
        res, err = create_policy_from_json(
            client, policy_file, name=name, description=description, force_create=force
        )
    elif policy_file.endswith(".py"):
        res, err = create_policy_from_dsl(
            client, policy_file, name=name, description=description, force_create=force
        )
    else:
        LOG.error("Unknown file format {}".format(policy_file))
        return
    if err:
        LOG.error(err["error"])
        return
    policy = res.json()
    policy_name = policy["metadata"]["name"]
    policy_uuid = policy["metadata"]["uuid"]
    policy_state = policy["status"]["resources"]["state"]
    LOG.info("Policy {} created successfully.".format(policy_name))
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()
    pc_ip = server_config["pc_ip"]
    pc_port = server_config["pc_port"]
    link = "https://{}:{}/console/#page/explore/calm/policies/approvals/{}".format(
        pc_ip, pc_port, policy_uuid
    )
    stdout_dict = {"name": policy_name, "link": link, "state": policy_state}
    click.echo(
        json.dumps(stdout_dict, indent=4, separators=(",", ": "), ensure_ascii=False)
    )


def get_policy_execution_list(
    policy_name, name, filter_by, limit, offset, quiet, all_items, out
):
    """Get the policies, optionally filtered by a string"""

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

    policy = get_policy(client, policy_name)
    uuid = policy["metadata"]["uuid"]
    res, err = client.policy.list_policy_execution(uuid=uuid, params=params)

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch policy executions from {}".format(pc_ip))
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
        click.echo(highlight_text("No policy executions found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "STATE",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]
    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]

        created_on = int(metadata["creation_time"]) // 1000000
        last_update_time = int(metadata["last_update_time"]) // 1000000

        table.add_row(
            [
                highlight_text(row["name"]),
                highlight_text(row["resources"]["state"]),
                "{}".format(arrow.get(created_on).humanize()),
                "{}".format(arrow.get(last_update_time).humanize()),
                highlight_text(metadata["uuid"]),
            ]
        )
    click.echo(table)


def describe_policy_execution(policy_name, out, uuid=""):
    """Displays approval request data"""

    client = get_api_client()
    policy_exec = get_policy_execution(client, policy_name, uuid=uuid)

    if out == "json":
        policy_exec.pop("status", None)
        click.echo(
            json.dumps(
                policy_exec, indent=4, separators=(",", ": "), ensure_ascii=False
            )
        )
        return

    click.echo("\n----Approval request Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(policy_exec["status"]["name"])
        + " (uuid: "
        + highlight_text(policy_exec["metadata"]["uuid"])
        + ")"
    )
    click.echo("Status: " + highlight_text(policy_exec["status"]["resources"]["state"]))
    click.echo(
        "Project: "
        + highlight_text(
            policy_exec["status"]["resources"]["project_reference"]["name"]
        )
    )
    created_on = int(policy_exec["metadata"]["creation_time"]) // 1000000
    past = arrow.get(created_on).humanize()
    click.echo(
        "Initiated: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    expires = int(policy_exec["metadata"]["expiry_time"]) // 1000000
    past = arrow.get(expires).humanize()
    click.echo(
        "Expires: {} ({})".format(
            highlight_text(time.ctime(created_on)), highlight_text(past)
        )
    )
    click.echo(
        "Requested By: "
        + highlight_text(policy_exec["status"]["resources"]["owner_reference"]["name"]),
        nl=False,
    )

    condition_list = (
        policy_exec.get("status").get("resources", {}).get("condition_list", [])
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
        policy_exec.get("status").get("resources", {}).get("approval_set_list", [])
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

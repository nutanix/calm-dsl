import time
import sys
import json
import arrow
import click
from ruamel import yaml

from calm.dsl.builtins import Ref
from calm.dsl.builtins.models.policy import Policy
from calm.dsl.builtins.models.policy_payload import create_policy_payload
from calm.dsl.builtins.models.helper.common import get_cur_context_project
from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .utils import highlight_text
from calm.dsl.constants import CACHE, POLICY
from calm.dsl.store import Cache
from calm.dsl.tools import get_module_from_file

LOG = get_logging_handle(__name__)


def describe_policy(policy_name, out):
    """Displays policy data"""

    client = get_api_client()
    policy = get_policy(client, policy_name)

    res, err = client.policy.read(policy["metadata"]["uuid"])
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Policy get failed for policy with uuid {}".format(
                policy["metadata"]["uuid"]
            )
        )
        sys.exit("Policy get failed on uuid={}".format(policy["metadata"]["uuid"]))

    policy = res.json()

    if out == "json":
        policy.pop("status", None)
        click.echo(json.dumps(policy, indent=4, separators=(",", ": ")))
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
    click.echo("Status: " + highlight_text(policy["status"]["resources"]["state"]))
    click.echo(
        "Owner: " + highlight_text(policy["metadata"]["owner_reference"]["name"]),
        nl=False,
    )
    click.echo(
        " Project: " + highlight_text(policy["metadata"]["project_reference"]["name"])
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
        click.echo(json.dumps(policy_payload, indent=4, separators=(",", ": ")))
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


def get_policy(client, policy_name):

    params = {"filter": "name=={}".format(policy_name)}
    res, err = client.policy.list(params=params)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        LOG.error(
            "Policy list call with params {} failed with error".format(
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
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

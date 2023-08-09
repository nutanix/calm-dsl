import time
import click
import json
import sys
from distutils.version import LooseVersion as LV
from prettytable import PrettyTable


from calm.dsl.api import get_api_client, network_group
from calm.dsl.builtins.models.network_group_tunnel import NetworkGroupTunnel
from calm.dsl.builtins.models.network_group_tunnel_payload import (
    create_network_group_tunnel_payload,
)
from calm.dsl.builtins.models.network_group_tunnel_vm_payload import (
    create_network_group_tunnel_vm_payload,
)
from calm.dsl.builtins.models.network_group_tunnel_vm_spec import (
    NetworkGroupTunnelVMSpec,
)
from calm.dsl.config import get_context
from calm.dsl.providers.base import get_provider

from .utils import highlight_text
from calm.dsl.tools import get_module_from_file
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.helper.common import (
    get_network_group,
    get_network_group_by_tunnel_name,
)
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE, NETWORK_GROUP_TUNNEL_TASK

LOG = get_logging_handle(__name__)


def get_network_groups(limit, offset, quiet, out):
    """Get the network groups, optionally filtered by a string"""

    client = get_api_client()
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()

    params = {"length": limit, "offset": offset}

    res, err = client.network_group.list(params=params)

    if err:
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch network group from {}".format(pc_ip))
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res["entities"]
    if not json_rows:
        click.echo(highlight_text("No network group found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "UUID",
        "NAME",
        "VPC",
        "TUNNEL",
        "ACCOUNT",
    ]
    # TODO: Add API call to show VPC name or read from Cache
    AhvVmProvider = get_provider("AHV_VM")
    AhvObj = AhvVmProvider.get_api_obj()

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]
        resources = row.get("resources", {})

        account_uuid = resources.get("account_reference", {}).get("uuid")
        res, err = client.account.read(account_uuid)
        if err:
            LOG.error(
                "Failed to find account with uuid:{}, Skipping".format(account_uuid)
            )
            continue

        account_info = res.json()
        if (
            account_info.get("status", {}).get("resources", {}).get("state")
            != "VERIFIED"
        ):
            LOG.warning(
                "Account with UUID: {} not in VERIFIED state, Skipping".format(
                    account_uuid
                )
            )
            continue

        account_name = account_info.get("metadata", {}).get("name")
        vpc_uuid = resources.get("platform_vpc_uuid_list", [])[0]
        vpc_filter = "(_entity_id_=={})".format(vpc_uuid)
        vpcs = AhvObj.vpcs(
            account_uuid=account_uuid, filter_query=vpc_filter, ignore_failures=True
        )
        LOG.debug(vpcs)
        if not vpcs or not vpcs.get("entities", []):
            LOG.error(
                "VPC with uuid:{} not found for account: {}".format(
                    vpc_uuid, account_name
                )
            )
            continue
        vpcs = vpcs.get("entities", [])
        vpc_name = vpcs[0].get("spec", {}).get("name")

        table.add_row(
            [
                highlight_text(metadata["uuid"]),
                highlight_text(metadata["name"]),
                highlight_text(vpc_name),
                highlight_text(resources.get("tunnel_reference", {}).get("name", "")),
                highlight_text(account_name),
            ]
        )
    click.echo(table)


def get_network_group_tunnels(limit, offset, quiet, out):
    """Get the Network Group Tunnels, optionally filtered by a string"""

    client = get_api_client()
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()

    params = {"length": limit, "offset": offset}
    params.update(
        {
            "nested_attributes": [
                "tunnel_name",
                "tunnel_vm_name",
                "app_uuid",
                "app_status",
            ]
        }
    )

    res, err = client.network_group.list(params=params)

    if err:
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch network group from {}".format(pc_ip))
        return

    res = res.json()
    total_matches = res["metadata"]["total_matches"]
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res["entities"]
    if not json_rows:
        click.echo(highlight_text("No network group found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "VPC",
        "STATE",
        "ACCOUNT",
        "APPLICATION_NAME",
        "TUNNEL_VM_NAME",
        "CREATED_ON",
        "UUID",
    ]
    # TODO: Add API call to show VPC name or read from Cache
    AhvVmProvider = get_provider("AHV_VM")
    AhvObj = AhvVmProvider.get_api_obj()

    for _row in json_rows:
        row = _row["status"]
        metadata = _row["metadata"]
        resources = row.get("resources", {})

        account_uuid = resources.get("account_reference", {}).get("uuid")
        res, err = client.account.read(account_uuid)
        if err:
            LOG.error(
                "Failed to find account with uuid:{}, Skipping".format(account_uuid)
            )
            continue
        LOG.debug("account information: {}".format(res.text))
        account_info = res.json()
        verified_acc = True
        if (
            account_info.get("status", {}).get("resources", {}).get("state")
            != "VERIFIED"
        ):
            LOG.warning(
                "Account with UUID: {} not in VERIFIED state, Skipping".format(
                    account_uuid
                )
            )
            verified_acc = False

        account_name = account_info.get("metadata", {}).get("name")
        vpc_uuid = resources.get("platform_vpc_uuid_list", [])[0]
        vpc_filter = "(_entity_id_=={})".format(vpc_uuid)
        vpc_name = "-"
        if verified_acc:
            vpcs = AhvObj.vpcs(
                account_uuid=account_uuid, filter_query=vpc_filter, ignore_failures=True
            )
            LOG.debug(vpcs)
            if not vpcs or not vpcs.get("entities", []):
                LOG.error(
                    "VPC with uuid:{} not found for account: {}".format(
                        vpc_uuid, account_name
                    )
                )
                continue
            vpcs = vpcs.get("entities", [])
            vpc_name = vpcs[0].get("spec", {}).get("name")

        app_uuid = resources.get("app_uuid")
        tunnel_vm_name = resources.get("tunnel_vm_name", "-")
        app_name = "-"
        if app_uuid:
            res, err = client.application.read(app_uuid)
            if err:
                LOG.warning("Application with UUID: {} not found, Skipping".format())
            app_info = res.json()
            app_name = app_info.get("metadata", {}).get("name")

        tunnel_uuid = resources.get("tunnel_reference", {}).get("uuid")
        tunnel_state = "-"
        if tunnel_uuid:
            res, err = client.tunnel.read(tunnel_uuid)
            if err:
                LOG.warning(
                    "Failed to get tunnel state information: {}, Skipping".format(
                        tunnel_uuid
                    )
                )
            tunnel_info = res.json()
            LOG.debug("tunnel: {}".format(tunnel_info))
            tunnel_state = tunnel_info.get("status", {}).get("state")
            tunnel_state = tunnel_state_mapper(tunnel_state)

        creation_time = int(tunnel_info.get("metadata").get("creation_time")) // 1000000

        table.add_row(
            [
                highlight_text(resources.get("tunnel_reference", {}).get("name", "-")),
                highlight_text(vpc_name),
                highlight_text(tunnel_state),
                highlight_text(account_name),
                highlight_text(app_name),
                highlight_text(tunnel_vm_name),
                highlight_text(time.ctime(creation_time)),
                highlight_text(resources.get("tunnel_reference", {}).get("uuid", "")),
            ]
        )
    click.echo(table)


def tunnel_state_mapper(state):
    tunnel_state_map = {
        "NOT_VALIDATED": "Connecting",
        "HEALTHY": "Connected",
        "UNHEALTHY": "Disconnected",
        "DELETING": "Deleting",
        "CONNECTING": "Connecting",
        "RECONNECTING": "Reconnecting",
        "DISCONNECTING": "Disconnecting",
    }
    return tunnel_state_map.get(state, "Unknown")


def describe_network_group(network_group_name, out):

    network_group = get_network_group(network_group_name)
    generate_describe_table(network_group, out)


def describe_network_group_tunnel(network_group_tunnel_name, out):

    network_group = get_network_group_from_tunnel_name(network_group_tunnel_name)
    generate_describe_table(network_group, out)


def generate_describe_table(network_group, out):

    client = get_api_client()
    network_group_name = network_group.get("metadata", {}).get("name")
    if out == "json":
        click.echo(json.dumps(network_group, indent=4, separators=(",", ": ")))
        return

    click.echo("\n----Network Group Summary----\n")
    click.echo(
        "Name: "
        + highlight_text(network_group_name)
        + " (uuid: "
        + highlight_text(network_group["metadata"]["uuid"])
        + ")"
    )
    network_group_resources = network_group["status"].get("resources", {})

    click.echo("State: " + highlight_text(network_group_resources["state"]))
    click.echo(
        "Owner: " + highlight_text(network_group["metadata"]["owner_reference"]["name"])
    )

    # created_on = arrow.get(network_group["metadata"]["creation_time"])
    # past = created_on.humanize()
    # click.echo(
    #    "Created on: {} ({})".format(
    #       highlight_text(time.ctime(created_on.timestamp)), highlight_text(past)
    #    )
    # )

    account = network_group_resources.get("account_reference", {})
    platform_vpcs = network_group_resources.get("platform_vpc_uuid_list", [])

    vpcCaches = []
    if platform_vpcs:

        for vpc in platform_vpcs:
            vpc_cache_data = Cache.get_entity_data_using_uuid(
                entity_type="ahv_vpc", uuid=vpc
            )
            vpcCaches.append(vpc_cache_data)
            if not vpc_cache_data:
                LOG.error("VPC (uuid={}) not found. Please update cache".format(vpc))
                sys.exit(-1)

        click.echo("\n\tVPC:\n\t--------------------")
        for vpc in vpcCaches:
            vpc_name = vpc["name"]
            vpc_uuid = vpc["uuid"]

            click.echo(
                "\tName: {} (uuid: {})".format(
                    highlight_text(vpc_name),
                    highlight_text(vpc_uuid),
                )
            )

            tunnel_uuid = network_group_resources.get("tunnel_reference", {}).get(
                "uuid"
            )
            if tunnel_uuid:
                res, err = client.tunnel.read(tunnel_uuid)
                if err:
                    LOG.error(err)
                    sys.exit(-1)

                tunnel_payload = res.json()
                tunnel_status = tunnel_payload.get("status", {})
                tunnel_name = tunnel_status.get("name")
                tunnel_state = tunnel_state_mapper(tunnel_status.get("state"))
                app_uuid = network_group_resources.get("app_uuid")

                res, err = client.application.read(app_uuid)
                if err:
                    LOG.error(
                        "Failed to fetch Tunnel Application due to {}".format(err)
                    )
                    sys.exit(-1)

                app = res.json()
                app_name = app.get("metadata", {}).get("name")

                click.echo("\n\tTunnel: \n\t--------------------")
                click.echo("\t" + "Name: " + highlight_text(tunnel_name))
                click.echo("\t" + "UUID: " + highlight_text(tunnel_uuid))
                click.echo("\t" + "State: " + highlight_text(tunnel_state))
                click.echo("\t" + "Application UUID: " + highlight_text(app_uuid))
                click.echo("\t" + "Application Name: " + highlight_text(app_name))

                tunnel_vm_name = network_group_resources.get("tunnel_vm_name")
                app_status = network_group_resources.get("app_status")
                click.echo("\n\t\tTunnel VM: \n\t\t--------------------")
                click.echo("\t\t" + "Name: " + highlight_text(tunnel_vm_name))
                click.echo("\t\t" + "Status: " + highlight_text(app_status))

    if account:
        account_uuid = account.get("uuid", "")
        account_payload = {}
        account_name = account.get("name", "")

        res, err = client.account.read(account_uuid)
        if err:
            LOG.error(err)
            sys.exit(-1)
        account_payload = res.json()

        resources = account_payload.get("status", {}).get("resources", {})
        if not account_name:
            account_name = resources.get("name", "")

        account_state = resources.get("state")
        click.echo("\n\tAccount: \n\t--------------------")
        click.echo("\t" + "Name: " + highlight_text(account_name))
        click.echo("\t" + "UUID: " + highlight_text(account_uuid))
        click.echo("\t" + "State: " + highlight_text(account_state))


def get_network_group_tunnel_module_from_file(network_group_tunnel_file):
    return get_module_from_file(
        "calm.dsl.user_network_group_tunnel", network_group_tunnel_file
    )


def get_network_group_tunnel_vm_module_from_file(network_group_tunnel_vm_file):
    return get_module_from_file(
        "calm.dsl.user_network_group_tunnel_vm", network_group_tunnel_vm_file
    )


def get_network_group_tunnel_class_from_module(user_network_group_tunnel_module):
    """Returns project class given a module"""

    UserProject = None
    for item in dir(user_network_group_tunnel_module):
        obj = getattr(user_network_group_tunnel_module, item)
        if isinstance(obj, type(NetworkGroupTunnel)):
            if obj.__bases__[0] == NetworkGroupTunnel:
                UserProject = obj

    return UserProject


def get_network_group_tunnel_vm_class_from_module(user_network_group_tunnel_vm_module):
    """Returns project class given a module"""

    UserProject = None
    for item in dir(user_network_group_tunnel_vm_module):
        obj = getattr(user_network_group_tunnel_vm_module, item)
        if isinstance(obj, type(NetworkGroupTunnelVMSpec)):
            if obj.__bases__[0] == NetworkGroupTunnelVMSpec:
                UserProject = obj

    return UserProject


def compile_network_group_tunnel_dsl_class(UserNetworkGroupTunnel):
    network_group_tunnel_payload, _ = create_network_group_tunnel_payload(
        UserNetworkGroupTunnel
    )
    return network_group_tunnel_payload.get_dict()


def compile_network_group_tunnel_vm_dsl_class(
    UserNetworkGroupTunnelVMSpec, network_group_tunnel_name
):
    network_group_tunnel_vm_payload, _ = create_network_group_tunnel_vm_payload(
        UserNetworkGroupTunnelVMSpec, network_group_tunnel_name
    )
    return network_group_tunnel_vm_payload.get_dict()


def watch_network_group_tunnel_launch_task(tunnel_setup_task, poll_interval):

    client = get_api_client()
    cnt = 0
    app_uuid = None
    milestone_reached = NETWORK_GROUP_TUNNEL_TASK.STATUS.QUEUED
    app_state = "provisioning"
    while True:
        LOG.info(
            "Fetching status of network group tunnel creation task: {}, state: {}".format(
                tunnel_setup_task, app_state
            )
        )

        res, err = client.network_group.read_pending_task(
            tunnel_setup_task, tunnel_setup_task
        )
        if err:
            LOG.error("Failed to read pending task status: {}".format(err))
            sys.exit(-1)

        res_json = res.json()
        # LOG.info("Response is : {}".format(res_json))
        app_uuid = res_json.get("status", {}).get("application_uuid", "")
        app_state = res_json.get("status", {}).get("state", "provisioning")
        milestone_reached = res_json.get("status", {}).get(
            "milestone", NETWORK_GROUP_TUNNEL_TASK.STATUS.QUEUED
        )

        if milestone_reached in NETWORK_GROUP_TUNNEL_TASK.TERMINAL_STATES:
            message_list = res_json.get("status", {}).get("message_list", [])
            if milestone_reached != NETWORK_GROUP_TUNNEL_TASK.STATUS.SUCCESS:
                if message_list:
                    LOG.error(message_list)
            LOG.info(
                "Network Group tunnel creation task reached terminal status: {}".format(
                    app_state
                )
            )
            return (milestone_reached, app_uuid)

        time.sleep(poll_interval)
        cnt += 1
        if cnt == 20:
            break

    LOG.info(
        "Task couldn't reached to terminal state in {} seconds. Exiting...".format(
            poll_interval * 20
        )
    )
    return (milestone_reached, app_uuid)


def watch_network_group_tunnel_app(account_uuid, network_group_name, poll_interval):

    cnt = 0
    network_group_json = {}
    app_state = "provisioning"
    while True:
        network_group_json = get_network_group_by_name(account_uuid, network_group_name)
        app_uuid = (
            network_group_json.get("status", {}).get("resources", {}).get("app_uuid")
        )
        app_state = (
            network_group_json.get("status", {}).get("resources", {}).get("app_status")
        )
        LOG.info("Application uuid: {}, status: {}".format(app_uuid, app_state))
        if app_state == "running":
            LOG.info(
                "Network Group Tunnel Provisioned successfully, wait for 5 minutes for Tunnel Sync"
            )
            return (network_group_json, app_state)

        time.sleep(poll_interval)
        cnt += 1
        if cnt == 20:
            break

    LOG.info(
        "Application did not reach Running status in {}. Exiting...".format(
            20 * poll_interval
        )
    )
    return (network_group_json, app_state)


def get_network_group_by_name(
    account_uuid=None, network_group_name=None, tunnel_name=None
):

    client = get_api_client()
    # LOG.info("Searching for Network Group using Network Group name:{}, Tunnel Name: {}".format(network_group_name, tunnel_name))
    filter_param = {}
    filter_query = []

    if account_uuid:
        filter_query.append("account_uuid=={}".format(account_uuid))

    if network_group_name:
        filter_query.append("name=={}".format(network_group_name))

    if filter_query:
        filter_param = {"filter": ";".join(filter_query)}

    filter_param.update(
        {
            "nested_attributes": [
                "tunnel_name",
                "tunnel_vm_name",
                "app_uuid",
                "app_status",
            ]
        }
    )

    res, err = client.network_group.list(params=filter_param)
    if err:
        LOG.error(
            "Failed to get Network Group Tunnel information due to {}".format(err)
        )
        sys.exit(-1)

    res_dict = res.json()
    network_group_json = {}
    for entity in res_dict.get("entities", []):
        if (
            network_group_name
            and entity.get("metadata", {}).get("name", "") == network_group_name
        ):
            network_group_json = entity
            break
        elif tunnel_name:
            api_tunnel_name = (
                entity.get("status", {}).get("resources", {}).get("tunnel_name")
            )
            if tunnel_name == api_tunnel_name:
                network_group_json = entity
                break

    return network_group_json


def create_network_group_tunnel_vm(tunnel_vm_payload, tunnel_name):

    client = get_api_client()

    network_group_json = get_network_group_by_tunnel_name(tunnel_name)

    network_group_uuid = network_group_json.get("metadata", {}).get("uuid")

    # Update tunnel reference in tunnel_vm_payload
    tunnel_reference = (
        network_group_json.get("status", {})
        .get("resources", {})
        .get("tunnel_reference", {})
    )
    tunnel_vm_payload["spec"]["resources"]["tunnel_reference"] = tunnel_reference

    res, err = client.network_group.reset_network_group_tunnel_vm(
        network_group_uuid, tunnel_vm_payload
    )
    if err:
        LOG.info("Failed to create network group tunnel VM due to :{}".format(err))
        sys.exit(-1)

    create_response = res.json()

    # Modify spec so that watch_tunnel_creation does not break
    network_group_json["spec"] = network_group_json["status"]

    watch_tunnel_creation(network_group_json, create_response)


def create_network_group_tunnel(payload):

    client = get_api_client()

    res, err = client.network_group.create_network_group_tunnel(payload)
    if err:
        LOG.info("Failed to create network group tunnel due to :{}".format(err))
        sys.exit(-1)

    response = res.json()

    return watch_tunnel_creation(payload, response)


def watch_tunnel_creation(payload, response):

    client = get_api_client()

    LOG.info("Tunnel setup task details: {}".format(response))
    tunnel_setup_task_uuid = response["request_id"]

    stdout_dict = {
        "name": payload["metadata"]["name"],
        "tunnel_setup_task_uuid": tunnel_setup_task_uuid,
        "tunnel_name": payload["spec"]["resources"]["tunnel_reference"]["name"],
        "tunnel_uuid": payload["spec"]["resources"]["tunnel_reference"]["uuid"],
    }

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    LOG.info("Polling on network group tunnel creation task")

    task_state, _ = watch_network_group_tunnel_launch_task(
        tunnel_setup_task_uuid, poll_interval=4
    )

    if task_state in NETWORK_GROUP_TUNNEL_TASK.FAILURE_STATES:
        LOG.exception(
            "Network Group Tunnel creation task went to {} state".format(task_state)
        )
        sys.exit(-1)

    # Now monitor the app state and wait for it to go into Terminal state because launch was successful
    account_uuid = payload["spec"]["resources"]["account_reference"]["uuid"]

    network_group_json, app_state = watch_network_group_tunnel_app(
        account_uuid, payload["metadata"]["name"], poll_interval=4
    )

    # Collect Tunnel Application information
    stdout_dict["application_status"] = app_state
    stdout_dict["application_uuid"] = (
        network_group_json.get("status", {}).get("resources", {}).get("app_uuid")
    )

    # Collect Tunnel Status information
    res, err = client.tunnel.read(
        payload["spec"]["resources"]["tunnel_reference"]["uuid"]
    )
    if err:
        LOG.error(err)
        sys.exit(-1)
    tunnel_json = res.json()

    tunnel_state = tunnel_json.get("status", {}).get("state")
    stdout_dict["tunnel_state"] = tunnel_state_mapper(tunnel_state)
    stdout_dict["tunne_vm_name"] = (
        network_group_json.get("status", {}).get("resources", {}).get("tunnel_vm_name")
    )

    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    return network_group_json


def create_network_group_tunnel_from_dsl(
    network_group_tunnel_file, tunnel_name="", description=""
):

    user_network_group_tunnel_module = get_network_group_tunnel_module_from_file(
        network_group_tunnel_file
    )

    UserProject = get_network_group_tunnel_class_from_module(
        user_network_group_tunnel_module
    )
    if UserProject is None:
        LOG.error("User project not found in {}".format(network_group_tunnel_file))
        return

    network_group_tunnel_payload = compile_network_group_tunnel_dsl_class(UserProject)

    if tunnel_name:
        network_group_tunnel_payload["metadata"]["name"] = tunnel_name + "_ng"
        network_group_tunnel_payload["spec"]["name"] = tunnel_name + "_ng"
        network_group_tunnel_payload["spec"]["resources"]["tunnel_reference"][
            "name"
        ] = tunnel_name

    LOG.debug("Payload: {}".format(network_group_tunnel_payload))

    network_group_json = create_network_group_tunnel(network_group_tunnel_payload)

    if network_group_json:
        LOG.info("Updating cache...")
        Cache.sync_table(CACHE.ENTITY.AHV_VPC)


def create_network_group_tunnel_vm_from_dsl(
    network_group_tunnel_vm_file, network_group_tunnel_name
):
    user_network_group_tunnel_vm_module = get_network_group_tunnel_vm_module_from_file(
        network_group_tunnel_vm_file
    )

    UserProject = get_network_group_tunnel_vm_class_from_module(
        user_network_group_tunnel_vm_module
    )
    if UserProject is None:
        LOG.error("User project not found in {}".format(network_group_tunnel_vm_file))
        return

    network_group_tunnel_vm_payload = compile_network_group_tunnel_vm_dsl_class(
        UserProject, network_group_tunnel_name
    )
    LOG.debug("Payload: {}".format(network_group_tunnel_vm_payload))

    network_group_json = create_network_group_tunnel_vm(
        network_group_tunnel_vm_payload, network_group_tunnel_name
    )

    if network_group_json:
        LOG.info("Updating cache...")
        Cache.sync_table(CACHE.ENTITY.AHV_VPC)


def get_network_group_from_tunnel_name(tunnel_name):
    network_group_json = get_network_group_by_name(None, None, tunnel_name)
    if not network_group_json:
        LOG.error("Failed to find tunnel with name: {}".format(tunnel_name))
        sys.exit(-1)
    return network_group_json


def delete_network_group_tunnel(network_group_tunnel_names):

    client = get_api_client()

    for tunnel_name in network_group_tunnel_names:
        network_group = get_network_group_from_tunnel_name(tunnel_name)

        network_group_uuid = network_group.get("metadata", {}).get("uuid")
        app_uuid = network_group.get("status", {}).get("resources", {}).get("app_uuid")
        res, err = client.application.read(app_uuid)
        if err:
            LOG.error("Failed to fetch Tunnel Application due to {}".format(err))
            sys.exit(-1)
        app_info = res.json()
        app_name = app_info.get("metadata", {}).get("name")

        tunnel_uuid = (
            network_group.get("status", {})
            .get("resources", {})
            .get("tunnel_reference", {})
            .get("uuid")
        )
        LOG.info(
            "Triggering Delete of Tunnel: {}, UUID: {}, Network Group UUID: {}".format(
                tunnel_name, tunnel_uuid, network_group_uuid
            )
        )
        res, err = client.network_group.delete_tunnel(network_group_uuid, tunnel_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        LOG.info("Delete of Network Group Tunnel triggered successfully")
        response = res.json()
        runlog_id = response["status"]["runlog_uuid"]

        LOG.info("Action runlog uuid: {}".format(runlog_id))
        LOG.info("Application UUID: {}".format(app_uuid))
        LOG.info("Application name: {}".format(app_name))

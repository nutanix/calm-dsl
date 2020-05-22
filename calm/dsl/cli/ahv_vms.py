import sys
import json
import time

from ruamel import yaml
import click
from prettytable import PrettyTable

from calm.dsl.config import get_config
from calm.dsl.api import get_api_client
from calm.dsl.tools import get_logging_handle
from calm.dsl.builtins import AhvVmResources
from calm.dsl.store import Cache

from .utils import get_module_from_file, highlight_text

LOG = get_logging_handle(__name__)


def get_ahv_vm_list(limit, offset, quiet):

    client = get_api_client()

    params = {"length": limit, "offset": offset}
    res, err = client.ahv_vm.list(params=params)

    if err:
        config = get_config()
        pc_ip = config["SERVER"]["pc_ip"]
        LOG.warning("Cannot fetch ahv_vms from {}".format(pc_ip))
        return

    json_rows = res.json()["entities"]
    if not json_rows:
        click.echo(highlight_text("No ahv_vm found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            row = _row["status"]
            click.echo(highlight_text(row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "HOST",
        "PROJECT",
        "OWNER",
        "HYPERVISOR",
        "MEMORY CAPACITY (GiB)",
        "IP ADDRESSES",
        "POWER STATE",
        "CLUSTER",
        "UUID",
    ]

    for row in json_rows:

        # Metadata section
        metadata = row["metadata"]

        project = None
        if "project_reference" in metadata:
            project = metadata["project_reference"]["name"]

        owner = None
        if "owner_reference" in metadata:
            owner = metadata["owner_reference"]["name"]

        # Status section
        status = row["status"]

        cluster = None
        if "cluster_reference" in status:
            cluster = status["cluster_reference"]["name"]

        name = None
        if "name" in status:
            name = status["name"]

        # Resources section
        resources = status["resources"]

        host = None
        if "host_reference" in resources:
            host = resources["host_reference"]["name"]

        hypervisor = None
        if "hypervisor_type" in resources:
            hypervisor = resources["hypervisor_type"]

        memory_capacity = None
        if "memory_size_mib" in resources:
            try:
                memory_capacity = int(resources["memory_size_mib"]) // 1024
            except:
                pass

        ip_address = None
        if "nic_list" in resources:
            nic_list = resources["nic_list"]
            try:
                # ToDo - get all IPs
                ip_address = nic_list[0]["ip_endpoint_list"][0]["ip"]
            except:
                pass

        power_state = None
        if "power_state" in resources:
            power_state = resources["power_state"]

        vm_uuid = None
        if "uuid" in metadata:
            vm_uuid = metadata["uuid"]

        table.add_row(
            [
                highlight_text(name),
                highlight_text(host),
                highlight_text(project),
                highlight_text(owner),
                highlight_text(hypervisor),
                highlight_text(memory_capacity),
                highlight_text(ip_address),
                highlight_text(power_state),
                highlight_text(cluster),
                highlight_text(vm_uuid),
            ]
        )

    click.echo(table)


def get_ahv_vm_module_from_file(vm_file):
    """Returns AHV VM module given a user AHV VM dsl file (.py)"""
    return get_module_from_file("calm.dsl.user_ahv_vm", vm_file)


def get_ahv_vm_class_from_module(user_ahv_vm_module):
    """Returns AHV VM class given a module"""

    UserAhvVm = None
    for item in dir(user_ahv_vm_module):
        obj = getattr(user_ahv_vm_module, item)
        if isinstance(obj, type(AhvVmResources)):
            if obj.__bases__[0] in (AhvVmResources,):
                UserAhvVm = obj

    return UserAhvVm


def create_ahv_vm_payload(UserAhvVm, categories=None):

    # Metadata section
    metadata = {"spec_version": 1, "kind": "vm", "name": UserAhvVm.__name__}

    # Add categories to metadata
    if categories:
        metadata["categories"] = categories

    # Add project reference to metadata
    config = get_config()
    project_name = config["PROJECT"].get("name", "default")
    project_cache_data = Cache.get_entity_data(entity_type="project", name=project_name)
    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
    project_uuid = project_cache_data.get("uuid", "")

    metadata["project_reference"] = {
        "kind": "project",
        "uuid": project_uuid,
        "name": project_name,
    }

    # Spec section
    spec = {
        "name": UserAhvVm.__name__,
        "description": UserAhvVm.__doc__ or "",
        "resources": UserAhvVm.get_dict(),
    }

    # Create v3 api payload
    ahv_vm_payload = {
        "metadata": metadata,
        "spec": spec,
    }

    return ahv_vm_payload


def compile_ahv_vm(bp_file, no_sync=False):

    # Sync only if no_sync flag is not set
    if not no_sync:
        LOG.info("Syncing cache")
        Cache.sync()

    user_ahv_vm_module = get_ahv_vm_module_from_file(bp_file)
    UserAhvVm = get_ahv_vm_class_from_module(user_ahv_vm_module)
    if UserAhvVm is None:
        return None

    ahv_vm_payload = None
    ahv_vm_payload = create_ahv_vm_payload(UserAhvVm)

    return ahv_vm_payload


def compile_ahv_vm_command(vm_file, out, no_sync=False):

    ahv_vm_payload = compile_ahv_vm(vm_file, no_sync)
    if ahv_vm_payload is None:
        LOG.error("VM not found in {}".format(vm_file))
        return

    if out == "json":
        click.echo(json.dumps(ahv_vm_payload, indent=4, separators=(",", ": ")))
    elif out == "yaml":
        click.echo(yaml.dump(ahv_vm_payload, default_flow_style=False))
    else:
        LOG.error("Unknown output format {} given".format(out))


def create_ahv_vm_command(vm_file, name):

    ahv_vm_payload = compile_ahv_vm(vm_file)
    if name:
        ahv_vm_payload["spec"]["name"] = name
        ahv_vm_payload["metadata"]["name"] = name

    client = get_api_client()
    res, err = client.ahv_vm.create(ahv_vm_payload)
    if err:
        LOG.error(err)
        sys.exit(-1)

    res = res.json()
    LOG.debug(json.dumps(res, indent=4, separators=(",", ": ")))

    execution_context = res["status"]["execution_context"]
    task_uuid = execution_context.get("task_uuid", "")

    poll_ahv_vm_task(task_uuid)


def get_ahv_vm(vm_name=None, vm_uuid=None):

    if not(vm_name or vm_uuid):
        LOG.error("Either vm_name or vm_uuid must be given")
        sys.exit(-1)
    
    client = get_api_client()
    if not vm_uuid:
        LOG.info("Searching for vm {}". format(vm_name))
        vm_name_uuids_map = client.ahv_vm.get_name_uuid_map({"length": 250})

        vm_uuids = vm_name_uuids_map.get(vm_name, [])
        if not isinstance(vm_uuids, list):
            vm_uuids = [vm_uuids]

        if vm_uuids:
            if len(vm_uuids) != 1:
                LOG.error("More than one ahv vm with name ({}) found. VM UUIDs: {}".format(vm_name, vm_uuids))
                sys.exit(-1)

            LOG.info("Ahv VM {} found ".format(vm_name))
            vm_uuid = vm_uuids[0]
        
        else:
            LOG.error("No Ahv vm with name {} found". format(vm_name))
            sys.exit(-1)
    
    res, err = client.ahv_vm.read(vm_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)
    
    vm_data = res.json()
    return vm_data


def delete_ahv_vm_command(name, vm_uuid=None):

    client = get_api_client()
    if not vm_uuid:
        vm_data = get_ahv_vm(vm_name=name)
        vm_uuid = vm_data["metadata"]["uuid"]

    LOG.info("Deleting Ahv vm with UUID ({})". format(vm_uuid))
    res, err = client.ahv_vm.delete(vm_uuid)
    if err:
        LOG.error("[{}] - {}".format(err["code"], err["error"]))
        sys.exit(-1)
    
    res = res.json()
    LOG.debug(json.dumps(res, indent=4, separators=(",", ": ")))

    execution_context = res["status"]["execution_context"]
    task_uuid = execution_context.get("task_uuid", "")

    poll_ahv_vm_task(task_uuid)


def poll_ahv_vm_task(task_uuid, poll_interval=10):

    client = get_api_client()
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        LOG.info("Fetching status of ahv vm task")
        # call status api
        res, err = client.ahv_vm.get_task(task_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        res = res.json()
        LOG.debug(json.dumps(res, indent=4, separators=(",", ": ")))
        status = res["status"]

        if status == "FAILED":
            LOG.info("FAILED")
            break

        elif status == "SUCCEEDED":
            LOG.info("SUCCEEDED")
            break

        elif status == "ABORTED":
            LOG.info("ABORTED")
            break

        else:
            LOG.info(status)

        count += poll_interval
        time.sleep(poll_interval)

    if count >= maxWait:
        LOG.info("Task not reached to terminal state in {}s". format(maxWait))

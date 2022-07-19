import os
import sys
import json
from jinja2 import Environment, PackageLoader
from Crypto.PublicKey import RSA

from calm.dsl.config import get_context
from calm.dsl.store import Cache
from calm.dsl.builtins import read_file
from calm.dsl.log import get_logging_handle
from calm.dsl.providers import get_provider
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)


def render_ahv_template(template, bp_name):

    ContextObj = get_context()

    project_config = ContextObj.get_project_config()
    project_name = project_config.get("name") or "default"
    project_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.PROJECT, name=project_name
    )
    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit(-1)

    # Fetch Nutanix_PC account registered
    project_accounts = project_cache_data["accounts_data"]
    account_uuids = project_accounts.get("nutanix_pc", [])
    if not account_uuids:
        LOG.error("No nutanix_pc account registered to project {}".format(project_name))

    # Fetch data for first account
    account_cache_data = Cache.get_entity_data_using_uuid(
        entity_type="account", uuid=account_uuids[0]
    )
    if not account_cache_data:
        LOG.error(
            "Account (uuid={}) not found. Please update cache".format(account_uuids[0])
        )
        sys.exit(-1)

    account_uuid = account_cache_data["uuid"]
    account_name = account_cache_data["name"]

    # Fetch whitelisted subnets
    whitelisted_subnets = project_cache_data["whitelisted_subnets"]
    if not whitelisted_subnets:
        LOG.error("No subnets registered to project {}".format(project_name))
        sys.exit(-1)

    account_subnets = whitelisted_subnets.get(account_uuid, [])
    if not account_subnets:
        LOG.error(
            "No subnets registered to project {} for Nutanix PC account {}.".format(
                project_name, account_name
            )
        )
        sys.exit(-1)

    # Fetch data for first subnet
    subnet_cache_data = Cache.get_entity_data_using_uuid(
        entity_type=CACHE.ENTITY.AHV_SUBNET,
        uuid=account_subnets[0],
        account_uuid=account_uuid,
    )
    if not subnet_cache_data:
        # Case when project have a subnet that is not available in subnets from registered account
        context_data = {
            "Project Whitelisted Subnets": account_subnets,
            "Account UUID": account_uuid,
            "Project Name": project_name,
        }
        LOG.debug(
            "Context data: {}".format(
                json.dumps(context_data, indent=4, separators=(",", ": "))
            )
        )
        LOG.error(
            "Subnet configuration mismatch in registered account's subnets and whitelisted subnets in project"
        )
        sys.exit(-1)

    cluster_name = subnet_cache_data["cluster_name"]
    default_subnet = subnet_cache_data["name"]
    LOG.info(
        "Using Nutanix PC account {}, cluster {}, subnet {}".format(
            account_name, cluster_name, default_subnet
        )
    )
    LOG.info("Rendering ahv template")
    text = template.render(
        bp_name=bp_name, subnet_name=default_subnet, cluster_name=cluster_name
    )

    return text.strip() + os.linesep


def render_single_vm_bp_ahv_template(template, bp_name):

    ContextObj = get_context()

    project_config = ContextObj.get_project_config()
    project_name = project_config.get("name") or "default"
    project_cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.PROJECT, name=project_name
    )
    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit(-1)

    # Fetch Nutanix_PC account registered
    project_accounts = project_cache_data["accounts_data"]
    account_uuids = project_accounts.get("nutanix_pc", [])
    if not account_uuids:
        LOG.error("No nutanix_pc account registered to project {}".format(project_name))

    # Fetch data for first account
    account_cache_data = Cache.get_entity_data_using_uuid(
        entity_type="account", uuid=account_uuids[0]
    )
    if not account_cache_data:
        LOG.error(
            "Account (uuid={}) not found. Please update cache".format(account_uuids[0])
        )
        sys.exit(-1)

    account_uuid = account_cache_data["uuid"]
    account_name = account_cache_data["name"]

    # Fetch whitelisted subnets
    whitelisted_subnets = project_cache_data["whitelisted_subnets"]
    if not whitelisted_subnets:
        LOG.error("No subnets registered to project {}".format(project_name))
        sys.exit(-1)

    account_subnets = whitelisted_subnets.get(account_uuid, [])
    if not account_subnets:
        LOG.error(
            "No subnets registered to project {} for Nutanix PC account {}.".format(
                project_name, account_name
            )
        )
        sys.exit(-1)

    # Fetch data for first subnet
    subnet_cache_data = Cache.get_entity_data_using_uuid(
        entity_type=CACHE.ENTITY.AHV_SUBNET,
        uuid=account_subnets[0],
        account_uuid=account_uuid,
    )
    if not subnet_cache_data:
        # Case when project have a subnet that is not available in subnets from registered account
        context_data = {
            "Project Whitelisted Subnets": account_subnets,
            "Account UUID": account_uuid,
            "Project Name": project_name,
        }
        LOG.debug(
            "Context data: {}".format(
                json.dumps(context_data, indent=4, separators=(",", ": "))
            )
        )
        LOG.error(
            "Subnet configuration mismatch in registered account's subnets and whitelisted subnets in project"
        )
        sys.exit(-1)

    cluster_name = subnet_cache_data["cluster_name"]
    default_subnet = subnet_cache_data["name"]

    # Fetch image for vm
    AhvVmProvider = get_provider("AHV_VM")
    AhvObj = AhvVmProvider.get_api_obj()
    try:
        res = AhvObj.images(account_uuid=account_uuid)
    except Exception:
        LOG.error(
            "Unable to fetch images for Nutanix_PC Account(uuid={})".format(
                account_uuid
            )
        )
        sys.exit(-1)

    # NOTE: Make sure you use `DISK` image in your jinja template
    vm_image = None
    for entity in res["entities"]:
        name = entity["status"]["name"]
        image_type = entity["status"]["resources"].get("image_type", None) or ""

        if image_type == "DISK_IMAGE":
            vm_image = name
            break

    if not vm_image:
        LOG.error("No Disk image found on account(uuid='{}')".format(account_uuid))
        sys.exit(-1)

    LOG.info(
        "Using Nutanix PC account {}, cluster {}, subnet {}".format(
            account_name, cluster_name, default_subnet
        )
    )
    LOG.info("Rendering ahv template")
    text = template.render(
        bp_name=bp_name,
        subnet_name=default_subnet,
        cluster_name=cluster_name,
        vm_image=vm_image,
    )

    return text.strip() + os.linesep


template_map = {
    "AHV_VM": {
        "MULTI_VM": ("ahv_blueprint.py.jinja2", render_ahv_template),
        "SINGLE_VM": (
            "ahv_single_vm_blueprint.py.jinja2",
            render_single_vm_bp_ahv_template,
        ),
    }
}


def render_blueprint_template(bp_name, provider_type, bp_type):

    if provider_type not in template_map:
        print(
            "Provider {} not supported. Using AHV_VM as provider".format(provider_type)
        )
        provider_type = "AHV_VM"

    schema_file, temp_render_helper = template_map.get(provider_type).get(bp_type)

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)

    return temp_render_helper(template, bp_name)


def create_bp_file(dir_name, bp_name, provider_type, bp_type):

    bp_text = render_blueprint_template(bp_name, provider_type, bp_type)
    bp_path = os.path.join(dir_name, "blueprint.py")

    LOG.info("Writing bp file to {}".format(bp_path))
    with open(bp_path, "w") as fd:
        fd.write(bp_text)


def create_cred_keys(dir_name):

    # Will create key via name centos/centos_pub

    key = RSA.generate(2048)

    # Write private key
    private_key = key.export_key("PEM")
    private_key_filename = os.path.join(dir_name, "centos")
    with open(private_key_filename, "wb") as fd:
        fd.write(private_key)
    os.chmod(private_key_filename, 0o600)

    # Write public key
    public_key = key.publickey().export_key("OpenSSH")
    public_key_filename = os.path.join(dir_name, "centos_pub")
    with open(public_key_filename, "wb") as fd:
        fd.write(public_key)
    os.chmod(public_key_filename, 0o600)


def create_scripts(dir_name):

    dir_path = os.path.dirname(os.path.realpath(__file__))
    scripts_dir = os.path.join(dir_path, "scripts")
    for script_file in os.listdir(scripts_dir):
        script_path = os.path.join(scripts_dir, script_file)
        data = read_file(script_path)

        with open(os.path.join(dir_name, script_file), "w+") as fd:
            fd.write(data)


def make_bp_dirs(dir_name, bp_name):

    bp_dir = "{}Blueprint".format(os.path.join(dir_name, bp_name))
    if not os.path.isdir(bp_dir):
        os.makedirs(bp_dir)

    local_dir = os.path.join(bp_dir, ".local")
    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    key_dir = os.path.join(local_dir, "keys")
    if not os.path.isdir(key_dir):
        os.makedirs(key_dir)

    script_dir = os.path.join(bp_dir, "scripts")
    if not os.path.isdir(script_dir):
        os.makedirs(script_dir)

    return (bp_dir, key_dir, script_dir)


def init_bp(bp_name, dir_name, provider_type, bp_type):

    bp_name = bp_name.strip().split()[0].title()
    bp_dir, key_dir, script_dir = make_bp_dirs(dir_name, bp_name)

    # Creating keys
    LOG.info("Generating keys for credentials")
    create_cred_keys(key_dir)

    # create scripts
    create_scripts(script_dir)

    create_bp_file(bp_dir, bp_name, provider_type, bp_type)

import os
import sys
import json
from jinja2 import Environment, PackageLoader
from Crypto.PublicKey import RSA

from calm.dsl.config import get_context
from calm.dsl.store import Cache
from calm.dsl.builtins import read_file
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_template(template, bp_name):

    ContextObj = get_context()

    project_config = ContextObj.get_project_config()
    project_name = project_config.get("name") or "default"
    project_cache_data = Cache.get_entity_data(entity_type="project", name=project_name)
    if not project_cache_data:
        LOG.error(
            "Project {} not found. Please run: calm update cache".format(project_name)
        )
        sys.exit(-1)

    # Fetch Nutanix_PC account registered
    project_accounts = project_cache_data["accounts_data"]
    account_uuid = project_accounts.get("nutanix_pc", "")
    if not account_uuid:
        LOG.error("No nutanix_pc account registered to project {}".format(project_name))

    # Fetch whitelisted subnets
    project_subnets = project_cache_data["whitelisted_subnets"]
    if not project_subnets:
        LOG.error("No subnets registered to project {}".format(project_name))
        sys.exit(-1)

    # Fetch data for first subnet
    subnet_cache_data = Cache.get_entity_data_using_uuid(
        entity_type="ahv_subnet", uuid=project_subnets[0], account_uuid=account_uuid
    )
    if not subnet_cache_data:
        # Case when project have a subnet that is not available in subnets from registered account
        context_data = {
            "Project Whitelisted Subnets": project_subnets,
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

    cluster_name = subnet_cache_data["cluster"]
    default_subnet = subnet_cache_data["name"]

    LOG.info("Rendering ahv template")
    text = template.render(
        bp_name=bp_name, subnet_name=default_subnet, cluster_name=cluster_name
    )

    return text.strip() + os.linesep


template_map = {"AHV_VM": ("ahv_blueprint.py.jinja2", render_ahv_template)}


def render_blueprint_template(bp_name, provider_type):

    if provider_type not in template_map:
        print(
            "Provider {} not supported. Using AHV_VM as provider".format(provider_type)
        )
        provider_type = "AHV_VM"

    schema_file, temp_render_helper = template_map.get(provider_type)

    loader = PackageLoader(__name__, "")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)

    return temp_render_helper(template, bp_name)


def create_bp_file(dir_name, bp_name, provider_type):

    bp_text = render_blueprint_template(bp_name, provider_type)
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


def init_bp(bp_name, dir_name, provider_type):

    bp_name = bp_name.strip().split()[0].title()
    bp_dir, key_dir, script_dir = make_bp_dirs(dir_name, bp_name)

    # Creating keys
    LOG.info("Generating keys for credentials")
    create_cred_keys(key_dir)

    # create scripts
    create_scripts(script_dir)

    create_bp_file(bp_dir, bp_name, provider_type)
